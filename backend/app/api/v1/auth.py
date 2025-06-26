"""
認証関連のAPIエンドポイント

このモジュールは、OAuth2.0認証フローのためのAPIエンドポイントを提供します。
認証URLの生成、コールバック処理、トークンのリフレッシュなどを処理します。
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import Optional
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
)
from app.core.security import get_current_user, get_current_active_user, create_access_token
from app.core.exceptions import ExternalAPIException
from app.models.user import User
from app.models.rbac import UserRole, Role
from app.core.utils import build_user_role_responses, QueryBuilder
from app.core.constants import AuthConstants, ErrorMessages
from app.core.exceptions import (
    AuthenticationException,
    TokenExpiredException,
    NotFoundException,
    handle_database_error
)
from app.core.database import transaction

router = APIRouter()

logger = logging.getLogger(__name__)


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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Backlog OAuth2.0認証URLを生成します

    このエンドポイントは、ユーザーをBacklogの認証ページにリダイレクトするための
    URLを生成します。CSRF攻撃を防ぐため、stateパラメータも生成して保存します。

    Returns:
        認証URLとstateを含むレスポンス
    """
    try:
        # 認証URLとstateを生成
        auth_url, state = backlog_oauth_service.get_authorization_url()

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
        raise HTTPException(
            status_code=500, detail=f"認証URLの生成に失敗しました: {str(e)}"
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
        raise HTTPException(status_code=400, detail="無効なstateパラメータです")

    if oauth_state.is_expired():
        logger.error(f"stateパラメータの有効期限切れ - state: {request.state}")
        db.delete(oauth_state)
        db.commit()
        raise HTTPException(
            status_code=400, detail="stateパラメータの有効期限が切れています"
        )

    try:
        # 認証コードをアクセストークンに交換
        logger.info("認証コードをアクセストークンに交換中...")
        token_data = await backlog_oauth_service.exchange_code_for_token(request.code)

        # ユーザー情報を取得
        logger.info("ユーザー情報を取得中...")
        user_info = await backlog_oauth_service.get_user_info(
            token_data["access_token"]
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

        # トークンを保存
        backlog_oauth_service.save_token(db, user.id, token_data)

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
        
        # UserRoleResponseのリストを作成
        user_roles = build_user_role_responses(user.user_roles)
        
        # レスポンスを作成
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoResponse(
                id=user.id,
                backlog_id=user.backlog_id,
                email=user.email,
                name=user.name,
                user_id=user.user_id,
                is_email_verified=user.is_email_verified,
                user_roles=user_roles
            ),
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認証処理中にエラーが発生しました。しばらく時間をおいて再度お試しください。"
        )


@router.post("/backlog/refresh", response_model=TokenResponse)
async def refresh_token(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
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
        # トークンをリフレッシュ
        new_token_data = await backlog_oauth_service.refresh_access_token(
            oauth_token.refresh_token
        )

        # 新しいトークンを保存
        backlog_oauth_service.save_token(db, current_user.id, new_token_data)

        # アプリケーション用のJWTトークンも新しく生成
        access_token = create_access_token(data={"sub": str(current_user.id)})

        # ユーザーのロール情報を取得
        user_with_roles = QueryBuilder.with_user_roles(
            db.query(User).filter(User.id == current_user.id)
        ).first()
        
        # UserRoleResponseのリストを作成
        user_roles = build_user_role_responses(user_with_roles.user_roles)
        
        # レスポンスを作成
        response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserInfoResponse(
                id=current_user.id,
                backlog_id=current_user.backlog_id,
                email=current_user.email,
                name=current_user.name,
                user_id=current_user.user_id,
                is_email_verified=current_user.is_email_verified,
                user_roles=user_roles
            ),
        )

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
        raise HTTPException(
            status_code=500, detail=f"トークンのリフレッシュに失敗しました: {str(e)}"
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
        raise HTTPException(
            status_code=401,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーのロール情報を取得
    from sqlalchemy.orm import joinedload
    from app.models.rbac import UserRole
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == current_user.id).first()
    
    # UserRoleResponseのリストを作成
    from app.schemas.auth import UserRoleResponse, RoleResponse
    user_roles = []
    for ur in user.user_roles:
        user_roles.append(UserRoleResponse(
            id=ur.id,
            role_id=ur.role_id,
            project_id=ur.project_id,
            role=RoleResponse(
                id=ur.role.id,
                name=ur.role.name,
                description=ur.role.description
            )
        ))
    
    return UserInfoResponse(
        id=current_user.id,
        backlog_id=current_user.backlog_id,
        email=current_user.email,
        name=current_user.name,
        user_id=current_user.user_id,
        is_email_verified=current_user.is_email_verified,
        user_roles=user_roles
    )


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
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # UserRoleResponseのリストを作成
    from app.schemas.auth import UserRoleResponse, RoleResponse
    user_roles = []
    for ur in user.user_roles:
        user_roles.append(UserRoleResponse(
            id=ur.id,
            role_id=ur.role_id,
            project_id=ur.project_id,
            role=RoleResponse(
                id=ur.role.id,
                name=ur.role.name,
                description=ur.role.description
            )
        ))
    
    return UserInfoResponse(
        id=user.id,
        backlog_id=user.backlog_id,
        email=user.email,
        name=user.name,
        user_id=user.user_id,
        is_email_verified=user.is_email_verified,
        user_roles=user_roles
    )


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
        raise HTTPException(
            status_code=400,
            detail="このメールアドレスは既に検証済みです"
        )
    
    # 他のユーザーが使用しているメールアドレスかチェック
    existing_user = db.query(User).filter(
        User.email == request.email,
        User.id != current_user.id,
        User.is_email_verified == True
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
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
        
        raise HTTPException(
            status_code=500,
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
        raise HTTPException(
            status_code=400,
            detail="無効な検証トークンです"
        )
    
    # トークンの有効期限を確認
    if user.email_verification_token_expires < datetime.now(ZoneInfo("Asia/Tokyo")):
        # 期限切れのトークンをクリア
        user.email_verification_token = None
        user.email_verification_token_expires = None
        db.commit()
        
        raise HTTPException(
            status_code=400,
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
        raise HTTPException(
            status_code=400,
            detail="メールアドレスは既に検証済みです"
        )
    
    if not current_user.email:
        raise HTTPException(
            status_code=400,
            detail="メールアドレスが設定されていません"
        )
    
    # 検証メールをリクエスト
    return await request_email_verification(
        EmailVerificationRequest(email=current_user.email),
        current_user,
        db
    )
