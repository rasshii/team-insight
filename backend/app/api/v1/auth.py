"""
認証関連のAPIエンドポイント

このモジュールは、Backlog OAuth2.0認証フローのためのAPIエンドポイントを提供します。
認証URLの生成、コールバック処理、トークンのリフレッシュなどを処理します。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
import secrets
from zoneinfo import ZoneInfo

from app.api.deps import get_db_session
from app.db.session import get_db_with_commit
from app.services.backlog_oauth import backlog_oauth_service
from app.services.auth_service import AuthService as BacklogAuthService
from app.models.auth import OAuthState, OAuthToken
from app.schemas.auth import (
    AuthorizationResponse,
    TokenResponse,
    TokenRefreshResponse,
    CallbackRequest,
    UserInfoResponse,
    UserRoleResponse,
    RoleResponse,
)
from app.core.security import (
    get_current_user,
    get_current_active_user,
    create_access_token,
    create_refresh_token,
    get_current_user_with_refresh_token,
)
from app.core.exceptions import ExternalAPIException
from app.models.user import User
from app.models.rbac import UserRole, Role
from app.core.utils import build_user_role_responses, QueryBuilder
from app.core.constants import AuthConstants, ErrorMessages
from app.core.exceptions import (
    AuthenticationException,
    TokenExpiredException,
    NotFoundException,
    AlreadyExistsException,
    ValidationException,
    DatabaseException,
    handle_database_error,
)


# 依存関係関数
def get_auth_service() -> BacklogAuthService:
    """AuthServiceのインスタンスを提供する依存関数"""
    return BacklogAuthService(backlog_oauth_service)


from app.core.database import transaction
from app.core.deps import get_response_formatter
from app.core.response_builder import ResponseBuilder, ResponseFormatter
from app.core.config import settings
import secrets
from app.core.auth_base import AuthResponseBuilder, CookieManager, TokenManager, AuthService as AuthBaseService

router = APIRouter()

logger = logging.getLogger(__name__)


def _build_user_response(user: User, access_token: str = None, db: Session = None) -> Dict[str, Any]:
    """
    統一的なユーザーレスポンスを構築

    Args:
        user: ユーザーオブジェクト（user_rolesがロード済みであること）
        access_token: アクセストークン（オプション）
        db: データベースセッション（backlog_space_key取得用）

    Returns:
        レスポンス辞書
    """
    # NOTE: この関数は既存のAPIとの互換性のために残しています
    # 新しいコードでは AuthResponseBuilder を使用してください
    user_roles = build_user_role_responses(user.user_roles)

    # OAuthTokenからbacklog_space_keyを取得
    backlog_space_key = None
    if db and user.id:
        from app.models.auth import OAuthToken

        oauth_token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).order_by(OAuthToken.created_at.desc()).first()
        if oauth_token:
            backlog_space_key = oauth_token.backlog_space_key
            logger.info(f"Found backlog_space_key for user {user.id}: {backlog_space_key}")
        else:
            logger.warning(f"No OAuth token found for user {user.id}")

    user_info = UserInfoResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        backlog_space_key=backlog_space_key,
        user_roles=user_roles,
        is_active=user.is_active,
    )

    response_data = {"user": user_info.model_dump()}

    if access_token:
        response_data["access_token"] = access_token
        response_data["token_type"] = "bearer"

    return response_data


def _cleanup_oauth_state(db: Session, oauth_state: Optional[OAuthState]) -> None:
    """
    OAuthStateのクリーンアップ処理

    エラー時に使用済みのstateを安全に削除します。
    削除に失敗してもエラーは発生させません。

    Args:
        db: データベースセッション
        oauth_state: 削除するOAuthStateオブジェクト
    """
    if oauth_state:
        try:
            db.delete(oauth_state)
            db.commit()
        except Exception as e:
            logger.warning(f"OAuthStateのクリーンアップに失敗しました: {str(e)}")
            db.rollback()


@router.get("/backlog/authorize", response_model=AuthorizationResponse)
async def get_authorization_url(
    space_key: Optional[str] = Query(None, description="BacklogのスペースキーOptional）環境変数がデフォルト"),
    force_account_selection: bool = Query(False, description="アカウント選択を強制するかどうか"),
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Backlog OAuth2.0認証URLを生成

    このエンドポイントは、ユーザーがBacklogアカウントで認証を行うための
    OAuth2.0認証URLを生成します。フロントエンドはこのURLにユーザーを
    リダイレクトさせ、Backlogの認証ページを表示します。

    認証:
        - 認証不要（未ログインユーザーも利用可能）
        - ログイン済みユーザーの場合は再認証として利用可能

    処理フロー:
        1. space_keyパラメータの検証（未指定の場合は環境変数から取得）
        2. CSRF攻撃防止用のstateトークンを生成（32バイトのランダム文字列）
        3. space_keyを含むstateデータを作成してBase64エンコード
        4. BacklogのOAuth認証URLを生成（stateパラメータを含む）
        5. stateをデータベースに保存（有効期限10分）
        6. 認証URLとstateをクライアントに返却

    Args:
        space_key: BacklogのスペースキーOptional）
                  未指定の場合は環境変数BACKLOG_SPACE_KEYの値を使用
        force_account_selection: アカウント選択を強制するかどうか（デフォルト: False）
                                Trueの場合、既にBacklogにログイン済みでも
                                アカウント選択画面が表示される
        db: データベースセッション（依存性注入）
        current_user: 現在のユーザー（依存性注入、未ログインの場合はNone）

    Returns:
        AuthorizationResponse: 認証URL、state、期待されるスペース情報を含むレスポンス
        {
            "authorization_url": "https://xxx.backlog.jp/OAuth2AccessRequest.action?...",
            "state": "base64エンコードされたstate文字列",
            "expected_space": "スペースキー"
        }

    Raises:
        ExternalAPIException: 認証URLの生成に失敗した場合

    Examples:
        リクエスト例1（スペースキー指定あり）:
            GET /api/v1/auth/backlog/authorize?space_key=myspace

        リクエスト例2（デフォルトスペースキー使用）:
            GET /api/v1/auth/backlog/authorize

        リクエスト例3（アカウント選択を強制）:
            GET /api/v1/auth/backlog/authorize?force_account_selection=true

        レスポンス例:
            {
                "authorization_url": "https://myspace.backlog.jp/OAuth2AccessRequest.action?...",
                "state": "eyJ0b2tlbiI6IkFCQy4uLiIsInNwYWNlX2tleSI6Im15c3BhY2UifQ==",
                "expected_space": "myspace"
            }

    Note:
        - stateはデータベースに10分間保存され、コールバック時に検証されます
        - stateにはCSRF対策用のトークンとspace_key情報が含まれます
        - 同じユーザーが複数回このエンドポイントを呼び出すと、複数のstateが生成されます
        - 未使用のstateは10分後に自動的に期限切れとなります

    セキュリティ考慮事項:
        - stateパラメータはCSRF攻撃を防ぐために必須です
        - stateはcryptographically secureな乱数生成器で生成されます
        - stateの有効期限は10分に制限されており、タイムアウト攻撃を防ぎます
    """
    import json
    import base64

    try:
        # space_keyが指定されていない場合は環境変数のデフォルト値を使用
        if not space_key:
            space_key = settings.BACKLOG_SPACE_KEY

        # stateを生成
        state_token = secrets.token_urlsafe(32)

        # space_keyを含むstateデータを作成
        state_data = {"token": state_token, "space_key": space_key}

        # stateデータをBase64エンコード
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

        # 認証URLを生成（space_keyを含める）
        auth_url, _ = backlog_oauth_service.get_authorization_url(
            space_key=space_key, state=state, force_account_selection=force_account_selection
        )

        # stateをデータベースに保存（10分間有効）
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=10)
        oauth_state = OAuthState(
            state=state,
            user_id=current_user.id if current_user else None,
            expires_at=expires_at,
        )
        db.add(oauth_state)
        db.commit()

        # クライアントに認証URLと共に期待されるスペース情報も返す
        response = AuthorizationResponse(authorization_url=auth_url, state=state)
        # レスポンスに追加情報を含める（クライアントでの検証用）
        response.expected_space = space_key
        return response
    except Exception as e:
        logger.error(f"認証URL生成エラー: {str(e)}", exc_info=True)
        raise ExternalAPIException(service="Backlog OAuth", detail="認証URLの生成に失敗しました")


@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(
    request: CallbackRequest,
    http_request: Request,
    db: Session = Depends(get_db_session),
    auth_service: BacklogAuthService = Depends(get_auth_service),
):
    """
    Backlog OAuth2.0認証コールバック処理

    Backlogの認証ページでユーザーが承認した後、このエンドポイントが
    呼び出されます。認証コードをアクセストークンに交換し、ユーザー情報を
    取得してシステムにログインさせます。

    認証:
        - 認証不要（このエンドポイント自体が認証プロセスの一部）

    処理フロー:
        1. stateパラメータを検証（CSRF攻撃対策）
        2. stateからspace_keyを抽出
        3. 認証コードをBacklogのアクセストークンに交換
        4. アクセストークンを使用してBacklogからユーザー情報を取得
        5. ユーザーをデータベースに作成または更新
        6. OAuthトークン（アクセストークン、リフレッシュトークン）をデータベースに保存
        7. 使用済みのstateをデータベースから削除
        8. JWTトークン（アプリケーション内部用）を生成
        9. ユーザーにデフォルトロール（MEMBER）を割り当て
        10. ログイン履歴とアクティビティログを記録
        11. JWTトークンをHttpOnly Cookieとレスポンスボディに設定して返却

    Args:
        request: 認証コードとstateを含むリクエスト
                code: Backlogから返された認証コード
                state: CSRF対策用のstateパラメータ
        http_request: HTTPリクエストオブジェクト（IPアドレスとUser-Agent取得用）
        db: データベースセッション（依存性注入）
        auth_service: 認証サービス（依存性注入）

    Returns:
        TokenResponse: アクセストークン、リフレッシュトークン、ユーザー情報を含むレスポンス
        {
            "access_token": "JWT形式のアクセストークン",
            "refresh_token": "JWT形式のリフレッシュトークン",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "backlog_id": "user123",
                "email": "user@example.com",
                "name": "ユーザー名",
                "user_id": "user_id",
                "backlog_space_key": "myspace",
                "user_roles": [...],
                "is_active": true
            }
        }

    Raises:
        ValidationException: stateパラメータの検証に失敗した場合
                           - stateが見つからない
                           - stateの有効期限が切れている
        ExternalAPIException: Backlog APIとの通信に失敗した場合
                            - トークン交換に失敗
                            - ユーザー情報の取得に失敗
        HTTPException: その他の予期しないエラーが発生した場合

    Examples:
        リクエスト例:
            POST /api/v1/auth/backlog/callback
            Content-Type: application/json
            {
                "code": "認証コード文字列",
                "state": "base64エンコードされたstate文字列"
            }

        レスポンス例:
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "backlog_id": "user123",
                    "email": "user@example.com",
                    "name": "山田太郎",
                    "user_id": "yamada",
                    "backlog_space_key": "myspace",
                    "user_roles": [
                        {
                            "id": 1,
                            "role_id": 1,
                            "project_id": null,
                            "role": {
                                "id": 1,
                                "name": "MEMBER",
                                "description": "一般メンバー"
                            }
                        }
                    ],
                    "is_active": true
                }
            }

    Note:
        - JWTトークンは2種類生成されます：
          1. アクセストークン（有効期限: 15分）: API認証用
          2. リフレッシュトークン（有効期限: 30日）: アクセストークン更新用
        - 両方のトークンはHttpOnly Cookieとして設定されます
        - 開発環境ではlocalhost間でCookieを共有するため、Domainが明示的に設定されます
        - 本番環境ではSameSite属性が追加されます
        - ログイン履歴にはIPアドレスとUser-Agentが記録されます

    セキュリティ考慮事項:
        - stateパラメータは必ず検証され、CSRF攻撃を防ぎます
        - 使用済みのstateは即座に削除され、再利用を防ぎます
        - JWTトークンはHttpOnly Cookieとして設定され、XSS攻撃を防ぎます
        - エラー発生時、内部エラーの詳細は隠蔽されます
        - トークンのリフレッシュ機能により、長期間のセッション維持が可能です

    Cookie管理:
        - アクセストークン: auth_token（有効期限: 15分）
        - リフレッシュトークン: refresh_token（有効期限: 30日）
        - 両方ともHttpOnly属性が設定され、JavaScriptからのアクセスは不可
        - 開発環境: Domain=localhost（ポート間での共有を可能にする）
        - 本番環境: SameSite=Lax（CSRF対策）
    """
    logger = logging.getLogger(__name__)

    logger.info(f"認証コールバック開始 - code: {request.code[:10]}..., state: {request.state}")

    # stateの検証
    oauth_state = auth_service.validate_oauth_state(db, request.state)

    try:
        # stateからspace_keyを取り出す
        space_key = auth_service.extract_space_key_from_state(request.state)

        # 認証コードをアクセストークンに交換
        token_data = await auth_service.exchange_code_for_token(request.code, space_key)

        # ユーザー情報を取得
        user_info = await auth_service.get_backlog_user_info(token_data["access_token"], space_key)

        # ユーザーの作成または更新
        user = auth_service.find_or_create_user(db, user_info)

        # トークンを保存（space_keyとユーザー情報も含めて保存）
        auth_service.save_oauth_token(db, user.id, token_data, space_key, user_info)

        # 使用済みのstateを削除
        auth_service.cleanup_oauth_state(db, oauth_state)

        # JWTトークンを生成（アプリケーション内での認証用）
        access_token, refresh_token = auth_service.create_jwt_tokens(user.id)

        logger.info(f"認証コールバック成功 - user_id: {user.id}")

        # ユーザーにデフォルトロールを割り当て
        user = auth_service.assign_default_role_if_needed(db, user)

        # ログイン履歴を記録
        from app.models.user_preferences import LoginHistory
        from app.services.activity_logger import ActivityLogger

        client_ip = http_request.client.host if http_request.client else None
        user_agent = http_request.headers.get("user-agent", "Unknown")

        login_history = LoginHistory(
            user_id=user.id, ip_address=client_ip, user_agent=user_agent, login_at=datetime.now(timezone.utc)
        )
        db.add(login_history)

        # アクティビティログを記録
        ActivityLogger.log_login(db, user, http_request)

        db.commit()

        # 統一的なユーザーレスポンスを構築
        response_data = _build_user_response(user, access_token, db=db)
        response_data["refresh_token"] = refresh_token

        # レスポンスを作成
        response = TokenResponse(**response_data)

        # Set-Cookieヘッダーを設定
        # 開発環境では異なるポート間でクッキーを共有するため、SameSiteを削除
        from app.core.config import settings

        # アクセストークンのCookie
        access_cookie_header = (
            f"{AuthConstants.COOKIE_NAME}={access_token}; "
            f"Path={AuthConstants.COOKIE_PATH}; HttpOnly; "
            f"Max-Age={AuthConstants.TOKEN_MAX_AGE}"
        )

        # リフレッシュトークンのCookie
        refresh_cookie_header = (
            f"refresh_token={refresh_token}; "
            f"Path={AuthConstants.COOKIE_PATH}; HttpOnly; "
            f"Max-Age={30 * 24 * 60 * 60}"  # 30日間
        )

        # 開発環境ではドメインを明示的に設定して、異なるポート間でクッキーを共有
        if settings.DEBUG:
            access_cookie_header += "; Domain=localhost"
            refresh_cookie_header += "; Domain=localhost"
        else:
            # 本番環境ではSameSiteを追加
            access_cookie_header += f"; SameSite={AuthConstants.COOKIE_SAMESITE}"
            refresh_cookie_header += f"; SameSite={AuthConstants.COOKIE_SAMESITE}"

        # Set-Cookieヘッダーは単一の文字列として連結
        headers = {}
        headers["Set-Cookie"] = f"{access_cookie_header}, {refresh_cookie_header}"

        return JSONResponse(content=response.model_dump(), headers=headers)

    except HTTPException:
        # HTTPExceptionはそのまま再raise（既に適切なステータスコードとメッセージが設定されている）
        db.rollback()
        _cleanup_oauth_state(db, oauth_state)
        raise
    except ExternalAPIException:
        # 外部APIエラーはそのまま再raise
        db.rollback()
        _cleanup_oauth_state(db, oauth_state)
        raise
    except Exception as e:
        # その他の予期しないエラー
        logger.error(f"認証処理で予期しないエラーが発生しました: {str(e)}", exc_info=True)
        db.rollback()
        _cleanup_oauth_state(db, oauth_state)
        # 内部エラーの詳細を隠蔽
        raise ExternalAPIException(
            service="Backlog OAuth", detail="認証処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
        )


@router.post("/backlog/refresh", response_model=TokenResponse)
async def refresh_token(db: Session = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    """
    BacklogのOAuthトークンをリフレッシュ

    Backlogのアクセストークンの有効期限が切れた場合や、期限が近い場合に
    リフレッシュトークンを使用して新しいアクセストークンを取得します。
    同時にアプリケーション内部用のJWTトークンも新しく生成します。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - 有効なJWTトークンが必要

    処理フロー:
        1. ユーザーのBacklog OAuthトークンをデータベースから取得
        2. リフレッシュトークンを使用してBacklogに新しいアクセストークンをリクエスト
        3. 新しいトークン情報をデータベースに保存（古いトークンは上書き）
        4. アプリケーション用の新しいJWTアクセストークンを生成
        5. ユーザー情報とトークンをレスポンスとして返却
        6. JWTトークンをHttpOnly Cookieに設定

    Args:
        db: データベースセッション（依存性注入）
        current_user: 現在のユーザー（依存性注入）

    Returns:
        TokenResponse: 新しいアクセストークンとユーザー情報を含むレスポンス
        {
            "access_token": "新しいJWTアクセストークン",
            "token_type": "bearer",
            "user": {
                "id": 1,
                "backlog_id": "user123",
                "email": "user@example.com",
                "name": "ユーザー名",
                "user_id": "user_id",
                "backlog_space_key": "myspace",
                "user_roles": [...],
                "is_active": true
            }
        }

    Raises:
        NotFoundException: BacklogのOAuthトークンが見つからない場合
        ExternalAPIException: Backlog APIとの通信に失敗した場合
                            - リフレッシュトークンが無効
                            - リフレッシュトークンの有効期限切れ
                            - Backlog APIがエラーを返した

    Examples:
        リクエスト例:
            POST /api/v1/auth/backlog/refresh
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "backlog_id": "user123",
                    "email": "user@example.com",
                    "name": "山田太郎",
                    "user_id": "yamada",
                    "backlog_space_key": "myspace",
                    "user_roles": [...],
                    "is_active": true
                }
            }

    Note:
        - このエンドポイントはBacklogのOAuthトークンをリフレッシュします
        - アプリケーション内部のJWTトークンのリフレッシュには /refresh エンドポイントを使用してください
        - リフレッシュトークンの有効期限は通常90日間です（Backlogの設定による）
        - リフレッシュトークンの有効期限が切れた場合は、再度OAuth認証が必要です
        - 新しいアクセストークンの有効期限は通常1時間です（Backlogの設定による）

    セキュリティ考慮事項:
        - リフレッシュトークンはデータベースに暗号化されずに保存されています
        - トークンのリフレッシュに成功すると、古いアクセストークンは無効になります
        - リフレッシュトークンは一度しか使用できません（Backlogの仕様）
    """
    # ユーザーのBacklogトークンを取得
    oauth_token = (
        db.query(OAuthToken)
        .filter(OAuthToken.user_id == current_user.id, OAuthToken.provider == AuthConstants.PROVIDER_BACKLOG)
        .first()
    )

    if not oauth_token:
        raise NotFoundException(resource="Backlogトークン", detail=ErrorMessages.TOKEN_NOT_FOUND)

    try:
        # space_keyを取得（既存のトークンから）
        space_key = oauth_token.backlog_space_key or settings.BACKLOG_SPACE_KEY

        # トークンをリフレッシュ
        new_token_data = await backlog_oauth_service.refresh_access_token(oauth_token.refresh_token, space_key=space_key)

        # 新しいトークンを保存（space_keyも含める）
        backlog_oauth_service.save_token(db, current_user.id, new_token_data, space_key=space_key)

        # アプリケーション用のJWTトークンも新しく生成
        access_token = create_access_token(data={"sub": str(current_user.id)})

        # ユーザーのロール情報を取得
        user_with_roles = QueryBuilder.with_user_roles(db.query(User).filter(User.id == current_user.id)).first()

        # 統一的なユーザーレスポンスを構築
        response_data = _build_user_response(user_with_roles, access_token)

        # レスポンスを作成
        response = TokenResponse(**response_data)

        # Set-Cookieヘッダーを設定
        # 開発環境では異なるポート間でクッキーを共有するため、SameSiteを削除
        from app.core.config import settings

        cookie_header = (
            f"{AuthConstants.COOKIE_NAME}={access_token}; "
            f"Path={AuthConstants.COOKIE_PATH}; HttpOnly; "
            f"Max-Age={AuthConstants.TOKEN_MAX_AGE}"
        )

        # 開発環境ではドメインを明示的に設定して、異なるポート間でクッキーを共有
        if settings.DEBUG:
            cookie_header += "; Domain=localhost"
        else:
            # 本番環境ではSameSiteを追加
            cookie_header += f"; SameSite={AuthConstants.COOKIE_SAMESITE}"

        return JSONResponse(
            content=response.model_dump(),
            headers={"Set-Cookie": cookie_header},
        )

    except Exception as e:
        logger.error(f"トークンリフレッシュエラー: {str(e)}", exc_info=True)
        raise ExternalAPIException(service="Backlog OAuth", detail="トークンのリフレッシュに失敗しました")


@router.get("/verify", response_model=UserInfoResponse)
async def verify_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db_session)):
    """
    JWTトークンの有効性を検証

    フロントエンドのミドルウェアがページ遷移時やアプリケーション起動時に
    このエンドポイントを呼び出し、ユーザーのログイン状態を確認します。
    トークンが有効であれば、最新のユーザー情報を返却します。

    認証:
        - 認証必須（有効なJWTトークンが必要）

    処理フロー:
        1. JWTトークンを検証（依存性注入で自動実行）
        2. トークンが有効な場合、ユーザー情報をデータベースから取得
        3. ユーザーのロール情報も含めて取得
        4. ユーザー情報をレスポンスとして返却

    Args:
        current_user: 現在のユーザー（依存性注入、トークン検証済み）
        db: データベースセッション（依存性注入）

    Returns:
        UserInfoResponse: ユーザー情報とロール情報
        {
            "id": 1,
            "backlog_id": "user123",
            "email": "user@example.com",
            "name": "ユーザー名",
            "user_id": "user_id",
            "backlog_space_key": "myspace",
            "user_roles": [
                {
                    "id": 1,
                    "role_id": 1,
                    "project_id": null,
                    "role": {
                        "id": 1,
                        "name": "MEMBER",
                        "description": "一般メンバー"
                    }
                }
            ],
            "is_active": true
        }

    Raises:
        AuthenticationException: トークンが無効または期限切れの場合
        HTTPException(401): 認証が必要な場合

    Examples:
        リクエスト例:
            GET /api/v1/auth/verify
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "id": 1,
                "backlog_id": "user123",
                "email": "user@example.com",
                "name": "山田太郎",
                "user_id": "yamada",
                "backlog_space_key": "myspace",
                "user_roles": [
                    {
                        "id": 1,
                        "role_id": 1,
                        "project_id": null,
                        "role": {
                            "id": 1,
                            "name": "MEMBER",
                            "description": "一般メンバー"
                        }
                    }
                ],
                "is_active": true
            }

    Note:
        - このエンドポイントは認証が必要なページへのアクセス時に自動的に呼び出されます
        - トークンの有効性チェックと同時に最新のユーザー情報を取得できます
        - ユーザーのis_active状態もチェックされます
        - backlog_space_keyはOAuthTokenテーブルから取得されます

    セキュリティ考慮事項:
        - トークンの検証は依存性注入（get_current_user）で自動的に行われます
        - トークンが改ざんされている場合は検証に失敗します
        - トークンの有効期限が切れている場合は401エラーを返します
    """
    if not current_user:
        raise AuthenticationException(detail="認証が必要です")

    # ユーザーのロール情報を取得
    user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == current_user.id)).first()

    # 統一的なユーザーレスポンスを構築
    response_data = _build_user_response(user, db=db)

    return response_data["user"]


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db_session)):
    """
    現在ログイン中のユーザー情報を取得

    認証済みユーザーの詳細情報を取得します。プロフィール画面や
    ユーザー設定画面で使用されます。

    認証:
        - 認証必須（アクティブなユーザーのみ）

    処理フロー:
        1. 現在のユーザーIDでデータベースから詳細情報を取得
        2. ロール情報をeager loadingで同時に取得（N+1問題を回避）
        3. Backlog space keyをOAuthTokenテーブルから取得
        4. ユーザー情報を整形して返却

    Args:
        current_user: 現在のアクティブユーザー（依存性注入）
        db: データベースセッション（依存性注入）

    Returns:
        UserInfoResponse: ユーザーの詳細情報とロール情報
        {
            "id": 1,
            "backlog_id": "user123",
            "email": "user@example.com",
            "name": "ユーザー名",
            "user_id": "user_id",
            "backlog_space_key": "myspace",
            "user_roles": [...],
            "is_active": true
        }

    Raises:
        NotFoundException: ユーザーが見つからない場合（通常は発生しない）

    Examples:
        リクエスト例:
            GET /api/v1/auth/me
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "id": 1,
                "backlog_id": "user123",
                "email": "user@example.com",
                "name": "山田太郎",
                "user_id": "yamada",
                "backlog_space_key": "myspace",
                "user_roles": [
                    {
                        "id": 1,
                        "role_id": 1,
                        "project_id": null,
                        "role": {
                            "id": 1,
                            "name": "MEMBER",
                            "description": "一般メンバー"
                        }
                    }
                ],
                "is_active": true
            }

    Note:
        - /verify エンドポイントとの違い: このエンドポイントはアクティブユーザーのみ許可
        - eager loadingにより、ロール情報を効率的に取得します
        - プロフィール情報の更新には別のエンドポイントを使用してください
    """
    from sqlalchemy.orm import joinedload
    from app.models.rbac import UserRole

    # ユーザー情報をロール情報と共に再取得（eager loading）
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.id == current_user.id)
        .first()
    )

    if not user:
        raise NotFoundException(resource="ユーザー")

    # 統一的なユーザーレスポンスを構築
    response_data = _build_user_response(user, db=db)

    return response_data["user"]


@router.post("/refresh")
async def refresh_jwt_token(
    response: Response,
    current_user: User = Depends(get_current_user_with_refresh_token),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    JWTトークンをリフレッシュ（アプリケーション内部用）

    アクセストークンの有効期限が切れた際に、リフレッシュトークンを使用して
    新しいアクセストークンとリフレッシュトークンのペアを生成します。
    これにより、ユーザーは再ログインすることなくセッションを継続できます。

    認証:
        - リフレッシュトークンが必要
        - アクセストークンは不要（期限切れでも可）

    処理フロー:
        1. リフレッシュトークンを検証（依存性注入で自動実行）
        2. 新しいアクセストークンを生成（有効期限: 15分）
        3. 新しいリフレッシュトークンを生成（有効期限: 30日）
        4. ユーザーのロール情報をデータベースから取得
        5. 両方のトークンをHttpOnly Cookieに設定
        6. トークンとユーザー情報をレスポンスとして返却

    Args:
        response: FastAPIレスポンスオブジェクト（Cookie設定用）
        current_user: リフレッシュトークンから取得したユーザー（依存性注入）
        db: データベースセッション（依存性注入）
        formatter: レスポンスフォーマッター（依存性注入）

    Returns:
        Dict[str, Any]: 成功メッセージ、新しいトークン、ユーザー情報
        {
            "success": true,
            "message": "トークンを更新しました",
            "data": {
                "access_token": "新しいJWTアクセストークン",
                "refresh_token": "新しいJWTリフレッシュトークン",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "backlog_id": "user123",
                    "email": "user@example.com",
                    "name": "ユーザー名",
                    "user_id": "user_id",
                    "backlog_space_key": "myspace",
                    "user_roles": [...],
                    "is_active": true
                }
            }
        }

    Raises:
        HTTPException(401): リフレッシュトークンが無効または期限切れの場合
        AuthenticationException: トークン検証に失敗した場合

    Examples:
        リクエスト例:
            POST /api/v1/auth/refresh
            Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "success": true,
                "message": "トークンを更新しました",
                "data": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "user": {
                        "id": 1,
                        "backlog_id": "user123",
                        "email": "user@example.com",
                        "name": "山田太郎",
                        "user_id": "yamada",
                        "backlog_space_key": "myspace",
                        "user_roles": [...],
                        "is_active": true
                    }
                }
            }

    Note:
        - このエンドポイントはアプリケーション内部のJWTトークンをリフレッシュします
        - BacklogのOAuthトークンのリフレッシュには /backlog/refresh を使用してください
        - リフレッシュトークンも新しいものに更新されます（トークンローテーション）
        - 古いリフレッシュトークンは使用できなくなります
        - フロントエンドのaxiosインターセプターから自動的に呼び出されます

    セキュリティ考慮事項:
        - リフレッシュトークンローテーション: セキュリティ向上のため、リフレッシュ時に新しいリフレッシュトークンも発行します
        - HttpOnly Cookie: XSS攻撃を防ぐため、トークンはJavaScriptからアクセスできません
        - 開発環境: Domain=localhostで異なるポート間での共有を可能にします
        - 本番環境: SameSite=LaxでCSRF攻撃を防ぎます
    """
    # 新しいアクセストークンを生成
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=timedelta(minutes=AuthConstants.TOKEN_MAX_AGE // 60)
    )

    # 新しいリフレッシュトークンを生成
    refresh_token = create_refresh_token(data={"sub": str(current_user.id)})

    # ユーザーのロール情報を取得
    user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == current_user.id)).first()

    # 統一的なユーザーレスポンスを構築
    response_data = _build_user_response(user, access_token, db=db)
    response_data["refresh_token"] = refresh_token

    # Cookieの設定（アクセストークン）
    response.set_cookie(
        key=AuthConstants.COOKIE_NAME,
        value=access_token,
        max_age=AuthConstants.TOKEN_MAX_AGE,
        path=AuthConstants.COOKIE_PATH,
        domain="localhost",
        httponly=True,
        samesite=AuthConstants.COOKIE_SAMESITE,
        secure=False,
    )

    # Cookieの設定（リフレッシュトークン）
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,  # 30日間
        path=AuthConstants.COOKIE_PATH,
        domain="localhost",
        httponly=True,
        samesite=AuthConstants.COOKIE_SAMESITE,
        secure=False,
    )

    return formatter.success(data=response_data, message="トークンを更新しました")


@router.post("/logout")
async def logout(
    response: Response,
    http_request: Request,
    formatter: ResponseFormatter = Depends(get_response_formatter),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    ログアウト処理

    ユーザーをログアウトさせ、アクセストークンとリフレッシュトークンの
    両方を削除します。ログアウトのアクティビティログも記録されます。

    認証:
        - 認証は任意（未ログインユーザーでも呼び出し可能）
        - ログイン済みの場合はアクティビティログを記録

    処理フロー:
        1. ユーザーがログイン中の場合、ログアウトのアクティビティログを記録
        2. アクセストークン（auth_token）のCookieを削除
        3. リフレッシュトークン（refresh_token）のCookieを削除
        4. 成功メッセージを返却

    Args:
        response: FastAPIレスポンスオブジェクト（Cookie削除用）
        http_request: HTTPリクエストオブジェクト（アクティビティログ用）
        formatter: レスポンスフォーマッター（依存性注入）
        current_user: 現在のユーザー（依存性注入、未ログインの場合はNone）
        db: データベースセッション（依存性注入）

    Returns:
        Dict[str, Any]: 成功メッセージ
        {
            "success": true,
            "message": "ログアウトしました"
        }

    Examples:
        リクエスト例:
            POST /api/v1/auth/logout
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "success": true,
                "message": "ログアウトしました"
            }

    Note:
        - このエンドポイントはCookieベースの認証に対応しています
        - サーバー側でトークンを無効化することはありません（JWTの特性上）
        - Cookieを削除することで、ブラウザからトークンが送信されなくなります
        - ログアウト後は再度OAuth認証が必要です
        - アクティビティログにはIPアドレスとUser-Agentが記録されます

    Cookie管理:
        - 削除されるCookie:
          1. auth_token: アクセストークン
          2. refresh_token: リフレッシュトークン
        - Cookie属性:
          - HttpOnly: JavaScriptからのアクセスを防止
          - Path: /（全てのパスで有効）
          - Secure: 本番環境でのみ有効（HTTPS必須）
          - SameSite: Lax（CSRF対策）

    セキュリティ考慮事項:
        - Cookieの削除はクライアント側で行われます
        - JWTトークン自体は有効期限まで技術的には有効です
        - セキュリティ上、アクセストークンの有効期限は短く設定されています（15分）
        - ログアウトのアクティビティログにより、不正アクセスの検知が可能です
    """
    # ログアウトのアクティビティログを記録（ユーザーがログイン中の場合のみ）
    if current_user:
        from app.services.activity_logger import ActivityLogger

        ActivityLogger.log_logout(db, current_user, http_request)
    # クッキーを削除（アクセストークン）
    response.delete_cookie(
        key=AuthConstants.COOKIE_NAME,  # "auth_token"を使用
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,  # 本番環境ではsecureを有効化
        samesite=AuthConstants.COOKIE_SAMESITE,
    )

    # クッキーを削除（リフレッシュトークン）
    response.delete_cookie(
        key="refresh_token",
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,
        samesite=AuthConstants.COOKIE_SAMESITE,
    )

    return formatter.success(message="ログアウトしました")
