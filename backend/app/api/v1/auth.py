"""
認証関連のAPIエンドポイント

このモジュールは、OAuth2.0認証フローのためのAPIエンドポイントを提供します。
認証URLの生成、コールバック処理、トークンのリフレッシュなどを処理します。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import logging
from zoneinfo import ZoneInfo

from app.db.session import get_db
from app.services.backlog_oauth import backlog_oauth_service
from app.models.auth import OAuthState, OAuthToken
from app.schemas.auth import (
    AuthorizationResponse,
    TokenResponse,
    CallbackRequest,
    UserInfoResponse,
    EmailVerificationRequest,
    EmailVerificationConfirmRequest,
    EmailVerificationResponse,
    UserRoleResponse,
    RoleResponse,
    SignupRequest,
    SignupResponse,
    LoginRequest,
)
from app.core.security import get_current_user, get_current_active_user, create_access_token, get_password_hash, verify_password
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
    handle_database_error
)
from app.core.database import transaction
from app.services.email import email_service
from app.core.utils import normalize_email, generate_hash
from app.core.deps import get_response_formatter
from app.core.response_builder import ResponseBuilder, ResponseFormatter
from app.core.config import settings
import secrets

router = APIRouter()

logger = logging.getLogger(__name__)


def _build_user_response(user: User, access_token: str = None) -> Dict[str, Any]:
    """
    統一的なユーザーレスポンスを構築
    
    Args:
        user: ユーザーオブジェクト（user_rolesがロード済みであること）
        access_token: アクセストークン（オプション）
        
    Returns:
        レスポンス辞書
    """
    # UserRoleResponseのリストを作成
    user_roles = build_user_role_responses(user.user_roles)
    
    # ユーザー情報の構築
    user_info = UserInfoResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_email_verified=user.is_email_verified,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        user_roles=user_roles
    )
    
    # レスポンスの構築
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


@router.post("/signup", response_model=SignupResponse)
async def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    メール/パスワードでの新規ユーザー登録
    
    Args:
        signup_data: サインアップ情報
        db: データベースセッション
        formatter: レスポンスフォーマッター
        
    Returns:
        サインアップレスポンス
        
    Raises:
        AlreadyExistsException: メールアドレスが既に使用されている場合
    """
    # メールアドレスを正規化
    email = normalize_email(signup_data.email)
    
    # 既存ユーザーのチェック
    existing_user = db.query(User).filter(
        User.email == email
    ).first()
    
    if existing_user:
        raise AlreadyExistsException(
            resource="メールアドレス",
            detail=f"{email}は既に登録されています"
        )
    
    # パスワードのハッシュ化
    hashed_password = get_password_hash(signup_data.password)
    
    # メール確認トークンの生成
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # 新規ユーザーの作成
    new_user = User(
        email=email,
        name=signup_data.name,
        hashed_password=hashed_password,
        is_active=True,
        is_email_verified=False,
        email_verification_token=verification_token,
        email_verification_token_expires=verification_expires,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # デフォルトロール（MEMBER）の割り当て
    member_role = db.query(Role).filter(Role.name == "MEMBER").first()
    if member_role:
        user_role = UserRole(
            user_id=new_user.id,
            role_id=member_role.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(user_role)
        db.commit()
    
    # メール確認メールの送信
    try:
        await email_service.send_verification_email(
            email=new_user.email,
            name=new_user.name,
            token=verification_token
        )
    except Exception as e:
        logger.error(f"メール送信エラー: {str(e)}")
        # メール送信に失敗してもユーザー登録は成功とする
    
    # ユーザー情報の構築
    user_info = UserInfoResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        is_email_verified=new_user.is_email_verified,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        user_roles=[],
        backlog_id=None,
        user_id=None
    )
    
    return formatter.created(
        data={
            "user": user_info.model_dump(),
            "requires_verification": True
        },
        message="アカウントが作成されました。メールアドレスの確認をお願いします。"
    )


@router.post("/login")
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    メール/パスワードでのログイン
    
    Args:
        login_data: ログイン情報
        response: FastAPIレスポンスオブジェクト
        db: データベースセッション
        formatter: レスポンスフォーマッター
        
    Returns:
        ログイン成功レスポンス
        
    Raises:
        AuthenticationException: 認証に失敗した場合
    """
    # メールアドレスを正規化
    email = normalize_email(login_data.email)
    
    # ユーザーの取得（ロール情報も含む）
    user = QueryBuilder.with_user_roles(
        db.query(User).filter(User.email == email)
    ).first()
    
    if not user or not user.hashed_password:
        raise AuthenticationException(
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    
    # パスワードの検証
    if not verify_password(login_data.password, user.hashed_password):
        raise AuthenticationException(
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    
    # アクティブユーザーかチェック
    if not user.is_active:
        raise AuthenticationException(
            detail="アカウントが無効化されています"
        )
    
    # JWTトークンの生成
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=AuthConstants.TOKEN_MAX_AGE // 60)
    )
    
    # 統一的なユーザーレスポンスを構築
    response_data = _build_user_response(user, access_token)
    
    # Cookieの設定
    response.set_cookie(
        key=AuthConstants.COOKIE_NAME,
        value=access_token,
        max_age=AuthConstants.TOKEN_MAX_AGE,
        path=AuthConstants.COOKIE_PATH,
        domain="localhost",  # 開発環境用に明示的にドメインを設定
        httponly=True,
        samesite=AuthConstants.COOKIE_SAMESITE,
        secure=False  # HTTPSの場合はTrue
    )
    
    return formatter.success(
        data=response_data,
        message="ログインに成功しました"
    )


@router.get("/backlog/authorize", response_model=AuthorizationResponse)
async def get_authorization_url(
    space_key: Optional[str] = Query(None, description="BacklogのスペースキーOptional）環境変数がデフォルト"),
    db: Session = Depends(get_db),
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
        auth_url, _ = backlog_oauth_service.get_authorization_url(space_key=space_key, state=state)

        # stateをデータベースに保存（10分間有効）
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=10)
        oauth_state = OAuthState(
            state=state,
            user_id=current_user.id if current_user else None,
            expires_at=expires_at,
        )
        db.add(oauth_state)
        db.commit()

        return AuthorizationResponse(authorization_url=auth_url, state=state)
    except Exception as e:
        logger.error(f"認証URL生成エラー: {str(e)}", exc_info=True)
        raise ExternalAPIException(
            service="Backlog OAuth",
            detail="認証URLの生成に失敗しました"
        )


@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(request: CallbackRequest, db: Session = Depends(get_db)):
    """
    Backlog OAuth2.0認証のコールバックを処理します

    Backlogから認証コードを受け取り、アクセストークンに交換します。
    また、CSRF攻撃を防ぐためstateパラメータを検証します。

    Args:
        request: 認証コードとstateを含むリクエスト

    Returns:
        アクセストークンとユーザー情報を含むレスポンス

    Raises:
        HTTPException: state検証失敗またはトークン取得失敗時
    """
    logger = logging.getLogger(__name__)

    logger.info(
        f"認証コールバック開始 - code: {request.code[:10]}..., state: {request.state}"
    )

    # stateの検証
    oauth_state = db.query(OAuthState).filter(OAuthState.state == request.state).first()

    if not oauth_state:
        logger.error(f"無効なstateパラメータ - state: {request.state}")
        # デバッグ用：現在のstateをすべて表示
        all_states = db.query(OAuthState).all()
        logger.debug(f"現在のstate一覧: {[s.state for s in all_states]}")
        raise ValidationException(detail="無効なstateパラメータです")

    if oauth_state.is_expired():
        logger.error(f"stateパラメータの有効期限切れ - state: {request.state}")
        db.delete(oauth_state)
        db.commit()
        raise ValidationException(
            detail="stateパラメータの有効期限が切れています"
        )

    try:
        # stateからspace_keyを取り出す
        import json
        import base64
        
        space_key = None
        try:
            # Base64デコード
            state_json = base64.urlsafe_b64decode(request.state.encode()).decode()
            state_data = json.loads(state_json)
            space_key = state_data.get("space_key")
            logger.info(f"stateからspace_keyを取得 - space_key: {space_key}")
        except Exception as e:
            logger.warning(f"stateのデコードに失敗（旧形式の可能性）: {str(e)}")
            # 旧形式のstateの場合は環境変数のデフォルト値を使用
            space_key = settings.BACKLOG_SPACE_KEY
        
        # 認証コードをアクセストークンに交換
        logger.info("認証コードをアクセストークンに交換中...")
        token_data = await backlog_oauth_service.exchange_code_for_token(request.code, space_key=space_key)

        # ユーザー情報を取得
        logger.info("ユーザー情報を取得中...")
        user_info = await backlog_oauth_service.get_user_info(
            token_data["access_token"],
            space_key=space_key
        )

        # ユーザーの作成または更新
        user = db.query(User).filter(User.backlog_id == user_info["id"]).first()
        if not user:
            # 新規ユーザーの作成
            logger.info(f"新規ユーザーを作成 - backlog_id: {user_info['id']}")
            user = User(
                backlog_id=user_info["id"],
                email=user_info.get("mailAddress"),
                name=user_info["name"],
                user_id=user_info["userId"],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            logger.info(f"既存ユーザーを使用 - user_id: {user.id}")

        # トークンを保存（space_keyも含めて保存）
        backlog_oauth_service.save_token(db, user.id, token_data, space_key=space_key)

        # 使用済みのstateを削除
        db.delete(oauth_state)
        db.commit()

        # JWTトークンを生成（アプリケーション内での認証用）
        access_token = create_access_token(data={"sub": str(user.id)})

        logger.info(f"認証コールバック成功 - user_id: {user.id}")

        # ユーザーのロール情報を取得
        user = QueryBuilder.with_user_roles(
            db.query(User).filter(User.id == user.id)
        ).first()
        
        # 新規ユーザーの場合、デフォルトロール（MEMBER）を割り当て
        if not user.user_roles:
            member_role = db.query(Role).filter(Role.name == "MEMBER").first()
            if member_role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=member_role.id,
                    project_id=None  # グローバルロール
                )
                db.add(user_role)
                db.commit()
                db.refresh(user)
                # ロール情報を再取得
                user = QueryBuilder.with_user_roles(
                    db.query(User).filter(User.id == user.id)
                ).first()
        
        # 統一的なユーザーレスポンスを構築
        response_data = _build_user_response(user, access_token)
        
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
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
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
    db: Session = Depends(get_db)
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
    response_data = _build_user_response(user)
    
    return response_data["user"]


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
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
    response_data = _build_user_response(user)
    
    return response_data["user"]


@router.post("/email/verify", response_model=EmailVerificationResponse)
async def request_email_verification(
    request: EmailVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    メールアドレス検証用のメールを送信します
    
    Args:
        request: メールアドレスを含むリクエスト
        
    Returns:
        検証メール送信結果
        
    Raises:
        HTTPException: メールアドレスが既に使用されている、またはメール送信失敗時
    """
    import secrets
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    from app.services.email import email_service
    from app.core.config import settings
    
    logger = logging.getLogger(__name__)
    
    # 既に検証済みの場合
    if current_user.is_email_verified and current_user.email == request.email:
        raise ValidationException(
            detail="このメールアドレスは既に検証済みです"
        )
    
    # 他のユーザーが使用しているメールアドレスかチェック
    existing_user = db.query(User).filter(
        User.email == request.email,
        User.id != current_user.id,
        User.is_email_verified == True
    ).first()
    
    if existing_user:
        raise AlreadyExistsException(
            resource="メールアドレス",
            detail="このメールアドレスは既に他のユーザーが使用しています"
        )
    
    # 検証トークンを生成
    verification_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )
    
    # ユーザー情報を更新
    current_user.email = request.email
    current_user.email_verification_token = verification_token
    current_user.email_verification_token_expires = expires_at
    current_user.is_email_verified = False
    current_user.email_verified_at = None
    
    db.commit()
    
    # 検証URLを作成
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"
    
    # メール送信
    try:
        success = email_service.send_verification_email(
            to_email=request.email,
            user_name=current_user.name,
            verification_url=verification_url
        )
        
        if not success:
            raise Exception("メール送信に失敗しました")
            
        logger.info(f"検証メール送信成功 - user_id: {current_user.id}, email: {request.email}")
        
        return EmailVerificationResponse(
            message="検証メールを送信しました。メールを確認してください。",
            email=request.email
        )
        
    except Exception as e:
        logger.error(f"検証メール送信エラー - user_id: {current_user.id}, error: {str(e)}")
        # トークンをクリア
        current_user.email_verification_token = None
        current_user.email_verification_token_expires = None
        db.commit()
        
        raise ExternalAPIException(
            service="メール送信",
            detail="メールの送信に失敗しました。しばらくしてから再度お試しください。"
        )


@router.post("/email/verify/confirm", response_model=EmailVerificationResponse)
async def confirm_email_verification(
    request: EmailVerificationConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    メールアドレスの検証を確認します
    
    Args:
        request: 検証トークンを含むリクエスト
        
    Returns:
        検証結果
        
    Raises:
        HTTPException: 無効なトークンまたは期限切れの場合
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from app.services.email import email_service
    
    logger = logging.getLogger(__name__)
    
    # トークンでユーザーを検索
    user = db.query(User).filter(
        User.email_verification_token == request.token
    ).first()
    
    if not user:
        raise ValidationException(
            detail="無効な検証トークンです"
        )
    
    # トークンの有効期限を確認
    if user.email_verification_token_expires < datetime.now(ZoneInfo("Asia/Tokyo")):
        # 期限切れのトークンをクリア
        user.email_verification_token = None
        user.email_verification_token_expires = None
        db.commit()
        
        raise TokenExpiredException(
            detail="検証トークンの有効期限が切れています。再度検証メールをリクエストしてください。"
        )
    
    # メールアドレスを検証済みに更新
    user.is_email_verified = True
    user.email_verified_at = datetime.now(ZoneInfo("Asia/Tokyo"))
    user.email_verification_token = None
    user.email_verification_token_expires = None
    
    db.commit()
    
    # 検証成功通知メールを送信
    try:
        email_service.send_verification_success_email(
            to_email=user.email,
            user_name=user.name
        )
    except Exception as e:
        # メール送信に失敗してもエラーにはしない
        logger.error(f"検証成功通知メール送信エラー - user_id: {user.id}, error: {str(e)}")
    
    logger.info(f"メールアドレス検証成功 - user_id: {user.id}, email: {user.email}")
    
    return EmailVerificationResponse(
        message="メールアドレスの検証が完了しました",
        email=user.email
    )


@router.post("/email/verify/resend", response_model=EmailVerificationResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    検証メールを再送信します
    
    Returns:
        再送信結果
        
    Raises:
        HTTPException: 既に検証済み、またはメールアドレスが設定されていない場合
    """
    if current_user.is_email_verified:
        raise ValidationException(
            detail="メールアドレスは既に検証済みです"
        )
    
    if not current_user.email:
        raise ValidationException(
            detail="メールアドレスが設定されていません"
        )
    
    # 検証メールをリクエスト
    return await request_email_verification(
        EmailVerificationRequest(email=current_user.email),
        current_user,
        db
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
    # クッキーを削除
    response.delete_cookie(
        key=AuthConstants.COOKIE_NAME,  # "auth_token"を使用
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,  # 本番環境ではsecureを有効化
        samesite=AuthConstants.COOKIE_SAMESITE
    )
    
    return formatter.success(
        message="ログアウトしました"
    )
