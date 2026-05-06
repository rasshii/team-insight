"""
認証関連の API エンドポイント (Phase 0: 組織切替対応)

主要エンドポイント:
- GET  /verify             : JWT 検証 + ユーザー情報
- GET  /me                 : 現在のアクティブユーザー情報
- POST /refresh            : refresh token によるトークン再発行 (revocation list 連携)
- POST /logout             : ログアウト (refresh token 失効 + Cookie クリア)
- POST /switch-organization: 組織切替 (旧 refresh 失効 + 新ペア発行)

Phase 1 で /login, /accept-invitation, /forgot-password, /reset-password,
/change-password を追加する想定。
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db_session
from app.core.auth_base import AuthResponseBuilder, CookieManager, TokenManager
from app.core.deps import get_response_formatter
from app.core.exceptions import AuthenticationException, NotFoundException
from app.core.jwt_revocation import (
    is_refresh_token_revoked,
    revoke_refresh_token,
)
from app.core.response_builder import ResponseFormatter
from app.core.security import calculate_remaining_seconds, decode_token
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schemas.auth import (
    SwitchOrganizationRequest,
    TokenRefreshResponse,
    UserInfoResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _user_with_memberships(db: Session, user_id: int) -> Optional[User]:
    """organization_memberships を eager load してユーザーを取得"""
    return (
        db.query(User)
        .options(
            joinedload(User.organization_memberships).joinedload(
                OrganizationMember.organization
            )
        )
        .filter(User.id == user_id)
        .first()
    )


def _extract_refresh_token(request: Request) -> Optional[str]:
    """Cookie 優先で refresh_token を取り出す"""
    token = request.cookies.get("refresh_token")
    if token:
        return token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return None


@router.get("/verify", response_model=UserInfoResponse)
def verify_token(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> UserInfoResponse:
    """JWT トークンの有効性を検証し、ユーザー情報を返す"""
    user = _user_with_memberships(db, current_user.id)
    if not user:
        raise AuthenticationException(detail="ユーザーが見つかりません")
    return UserInfoResponse.model_validate(AuthResponseBuilder.build_user_response(user))


@router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> UserInfoResponse:
    """現在ログイン中のアクティブユーザー情報を取得"""
    user = _user_with_memberships(db, current_user.id)
    if not user:
        raise NotFoundException(resource="ユーザー")
    return UserInfoResponse.model_validate(AuthResponseBuilder.build_user_response(user))


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_jwt_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db_session),
) -> TokenRefreshResponse:
    """
    JWT アクセストークンとリフレッシュトークンをリフレッシュ

    リフレッシュトークンローテーション + revocation list を実装。
    """
    refresh_token = _extract_refresh_token(request)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンが必要です",
        )

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンタイプです",
        )

    jti = payload.get("jti")
    if await is_refresh_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="リフレッシュトークンが失効しています",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンです",
        )

    user = _user_with_memberships(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています",
        )

    active_org_id = payload.get("active_org_id")
    access_token, new_refresh, _new_jti = TokenManager.generate_tokens(
        user, active_org_id=active_org_id
    )

    # 旧 refresh を revocation list に登録 (token rotation)
    if jti:
        ttl = calculate_remaining_seconds(payload)
        await revoke_refresh_token(jti, ttl)

    CookieManager.set_auth_cookies(response, access_token, new_refresh)

    return TokenRefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        active_org_id=active_org_id,
    )


@router.post("/switch-organization", response_model=TokenRefreshResponse)
async def switch_organization(
    payload: SwitchOrganizationRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> TokenRefreshResponse:
    """
    アクティブ組織を切り替えて新しいトークンペアを発行する (Phase 0)

    切替条件:
    - 対象組織のメンバーであること (System Admin はバイパス)
    - 旧 refresh token を Redis revocation list に登録して即座に失効させる
    """
    if not (
        current_user.is_system_admin
        or current_user.is_member_of_organization(payload.organization_id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この組織への切り替え権限がありません",
        )

    user = _user_with_memberships(db, current_user.id)
    assert user is not None

    # 旧 refresh を失効
    old_refresh = _extract_refresh_token(request)
    if old_refresh:
        try:
            old_payload = decode_token(old_refresh)
            old_jti = old_payload.get("jti")
            if old_jti:
                ttl = calculate_remaining_seconds(old_payload)
                await revoke_refresh_token(old_jti, ttl)
        except HTTPException:
            # 旧トークンが無効な場合は単に新発行する
            pass

    access_token, new_refresh, _ = TokenManager.generate_tokens(
        user, active_org_id=payload.organization_id
    )

    CookieManager.set_auth_cookies(response, access_token, new_refresh)

    return TokenRefreshResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        active_org_id=payload.organization_id,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    formatter: ResponseFormatter = Depends(get_response_formatter),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """ログアウト処理 (refresh token revocation + Cookie クリア)"""
    refresh_token = _extract_refresh_token(request)
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                ttl = calculate_remaining_seconds(payload)
                await revoke_refresh_token(jti, ttl)
        except HTTPException:
            pass

    if current_user:
        try:
            from app.services.activity_logger import ActivityLogger

            ActivityLogger.log_logout(db, current_user, request)
        except Exception:
            logger.warning("Failed to log logout activity", exc_info=True)

    CookieManager.clear_auth_cookies(response)
    return formatter.success(message="ログアウトしました")
