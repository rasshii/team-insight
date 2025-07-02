"""
認証関連のAPIエンドポイント

このモジュールは、Backlog OAuth2.0認証フローのためのAPIエンドポイントを提供します。
認証URLの生成、コールバック処理、トークンのリフレッシュなどを処理します。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
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
from app.core.security import get_current_user, get_current_active_user, create_access_token, create_refresh_token, get_current_user_with_refresh_token
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
    handle_database_error
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
from app.core.auth_base import (
    AuthResponseBuilder,
    CookieManager,
    TokenManager,
    AuthService as AuthBaseService
)

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
        oauth_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id
        ).order_by(OAuthToken.created_at.desc()).first()
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
        is_email_verified=True,  # Backlog OAuth認証のみなので常にTrue
        backlog_space_key=backlog_space_key,
        user_roles=user_roles
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
    Backlog OAuth2.0認証URLを生成します

    このエンドポイントは、ユーザーをBacklogの認証ページにリダイレクトするための
    URLを生成します。CSRF攻撃を防ぐため、stateパラメータも生成して保存します。

    Args:
        space_key: BacklogのスペースキーOptional）環境変数がデフォルト

    Returns:
        認証URLとstateを含むレスポンス
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
        state_data = {
            "token": state_token,
            "space_key": space_key
        }
        
        # stateデータをBase64エンコード
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # 認証URLを生成（space_keyを含める）
        auth_url, _ = backlog_oauth_service.get_authorization_url(
            space_key=space_key, 
            state=state,
            force_account_selection=force_account_selection
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
        raise ExternalAPIException(
            service="Backlog OAuth",
            detail="認証URLの生成に失敗しました"
        )

@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(
    request: CallbackRequest, 
    db: Session = Depends(get_db_session),
    auth_service: BacklogAuthService = Depends(get_auth_service)
):
    """
    Backlog OAuth2.0認証のコールバックを処理します

    Backlogから認証コードを受け取り、アクセストークンに交換します。
    また、CSRF攻撃を防ぐためstateパラメータを検証します。

    Args:
        request: 認証コードとstateを含むリクエスト
        db: データベースセッション
        auth_service: 認証サービス

    Returns:
        アクセストークンとユーザー情報を含むレスポンス

    Raises:
        ValidationException: state検証失敗時
        ExternalAPIException: トークン取得失敗時
    """
    logger = logging.getLogger(__name__)

    logger.info(
        f"認証コールバック開始 - code: {request.code[:10]}..., state: {request.state}"
    )

    # stateの検証
    oauth_state = auth_service.validate_oauth_state(db, request.state)

    try:
        # stateからspace_keyを取り出す
        space_key = auth_service.extract_space_key_from_state(request.state)
        
        # 認証コードをアクセストークンに交換
        token_data = await auth_service.exchange_code_for_token(request.code, space_key)

        # ユーザー情報を取得
        user_info = await auth_service.get_backlog_user_info(
            token_data["access_token"],
            space_key
        )

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
        
        return JSONResponse(
            content=response.model_dump(),
            headers=headers
        )

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
            service="Backlog OAuth",
            detail="認証処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
        )

@router.post("/backlog/refresh", response_model=TokenResponse)
async def refresh_token(
    db: Session = Depends(get_db_session), current_user: User = Depends(get_current_active_user)
):
    """
    Backlogのアクセストークンをリフレッシュします

    保存されているリフレッシュトークンを使用して、
    新しいアクセストークンを取得します。

    Returns:
        新しいアクセストークンを含むレスポンス

    Raises:
        HTTPException: トークンが見つからない、またはリフレッシュ失敗時
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
        new_token_data = await backlog_oauth_service.refresh_access_token(
            oauth_token.refresh_token,
            space_key=space_key
        )

        # 新しいトークンを保存（space_keyも含める）
        backlog_oauth_service.save_token(db, current_user.id, new_token_data, space_key=space_key)

        # アプリケーション用のJWTトークンも新しく生成
        access_token = create_access_token(data={"sub": str(current_user.id)})

        # ユーザーのロール情報を取得
        user_with_roles = QueryBuilder.with_user_roles(
            db.query(User).filter(User.id == current_user.id)
        ).first()
        
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
            headers={
                "Set-Cookie": cookie_header
            },
        )

    except Exception as e:
        logger.error(f"トークンリフレッシュエラー: {str(e)}", exc_info=True)
        raise ExternalAPIException(
            service="Backlog OAuth",
            detail="トークンのリフレッシュに失敗しました"
        )


@router.get("/verify", response_model=UserInfoResponse)
async def verify_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    JWTトークンの有効性を確認し、ユーザー情報を返す
    
    このエンドポイントは、フロントエンドのミドルウェアから呼び出され、
    トークンが有効かどうかを確認するために使用されます。
    """
    if not current_user:
        raise AuthenticationException(
            detail="認証が必要です"
        )
    
    # ユーザーのロール情報を取得
    user = QueryBuilder.with_user_roles(
        db.query(User).filter(User.id == current_user.id)
    ).first()
    
    # 統一的なユーザーレスポンスを構築
    response_data = _build_user_response(user, db=db)
    
    return response_data["user"]


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
):
    """
    現在ログイン中のユーザー情報を取得します

    Returns:
        ユーザー情報（ロール情報を含む）
    """
    from sqlalchemy.orm import joinedload
    from app.models.rbac import UserRole
    
    # ユーザー情報をロール情報と共に再取得（eager loading）
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == current_user.id).first()
    
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
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    JWTトークンをリフレッシュします

    リフレッシュトークンを使用して新しいアクセストークンとリフレッシュトークンを生成します。

    Args:
        response: FastAPIレスポンスオブジェクト
        current_user: リフレッシュトークンから取得したユーザー
        db: データベースセッション
        formatter: レスポンスフォーマッター

    Returns:
        新しいトークンとユーザー情報を含むレスポンス

    Raises:
        HTTPException: リフレッシュトークンが無効な場合
    """
    # 新しいアクセストークンを生成
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=AuthConstants.TOKEN_MAX_AGE // 60)
    )
    
    # 新しいリフレッシュトークンを生成
    refresh_token = create_refresh_token(
        data={"sub": str(current_user.id)}
    )
    
    # ユーザーのロール情報を取得
    user = QueryBuilder.with_user_roles(
        db.query(User).filter(User.id == current_user.id)
    ).first()
    
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
        secure=False
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
        secure=False
    )
    
    return formatter.success(
        data=response_data,
        message="トークンを更新しました"
    )


@router.post("/logout")
async def logout(
    response: Response,
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    ログアウト処理
    
    HttpOnlyクッキーからアクセストークンを削除します。
    """
    # クッキーを削除（アクセストークン）
    response.delete_cookie(
        key=AuthConstants.COOKIE_NAME,  # "auth_token"を使用
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,  # 本番環境ではsecureを有効化
        samesite=AuthConstants.COOKIE_SAMESITE
    )
    
    # クッキーを削除（リフレッシュトークン）
    response.delete_cookie(
        key="refresh_token",
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,
        samesite=AuthConstants.COOKIE_SAMESITE
    )
    
    return formatter.success(
        message="ログアウトしました"
    )
