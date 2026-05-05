"""
認証関連のAPIエンドポイント

このモジュールは、JWT ベースの認証エンドポイントを提供します。
Backlog OAuth 関連エンドポイントは Phase 6 で削除済み。
Phase 1 (ID/パスワード認証) で /login, /accept-invitation, /forgot-password,
/reset-password, /change-password を追加する。
"""

from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db_session, get_current_active_user
from app.core.config import settings
from app.core.constants import AuthConstants
from app.core.deps import get_response_formatter
from app.core.exceptions import AuthenticationException, NotFoundException
from app.core.response_builder import ResponseFormatter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_user_with_refresh_token,
)
from app.core.utils import QueryBuilder, build_user_role_responses
from app.models.rbac import UserRole
from app.models.user import User
from app.schemas.auth import TokenResponse, UserInfoResponse


router = APIRouter()


def _build_user_response(user: User, access_token: Optional[str] = None) -> Dict[str, Any]:
    """統一的なユーザーレスポンスを構築"""
    user_roles = build_user_role_responses(user.user_roles)

    user_info = UserInfoResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        user_roles=user_roles,
        is_active=user.is_active,
    )

    response_data: Dict[str, Any] = {"user": user_info.model_dump()}
    if access_token:
        response_data["access_token"] = access_token
        response_data["token_type"] = "bearer"
    return response_data


@router.get("/verify", response_model=UserInfoResponse)
async def verify_token(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> UserInfoResponse:
    """JWTトークンの有効性を検証し、現在のユーザー情報を返す"""
    if not current_user:
        raise AuthenticationException(detail="認証が必要です")

    user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == current_user.id)).first()
    response_data = _build_user_response(user)
    return response_data["user"]


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> UserInfoResponse:
    """現在ログイン中のアクティブユーザー情報を取得"""
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.id == current_user.id)
        .first()
    )
    if not user:
        raise NotFoundException(resource="ユーザー")

    response_data = _build_user_response(user)
    return response_data["user"]


@router.post("/refresh")
async def refresh_jwt_token(
    response: Response,
    current_user: User = Depends(get_current_user_with_refresh_token),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    JWT アクセストークンとリフレッシュトークンをリフレッシュ

    リフレッシュトークンローテーションを実装。
    """
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=AuthConstants.TOKEN_MAX_AGE // 60),
    )
    refresh_token = create_refresh_token(data={"sub": str(current_user.id)})

    user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == current_user.id)).first()
    response_data = _build_user_response(user, access_token)
    response_data["refresh_token"] = refresh_token

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
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=30 * 24 * 60 * 60,
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
    """ログアウト処理 (Cookie 削除 + アクティビティログ記録)"""
    if current_user:
        from app.services.activity_logger import ActivityLogger

        ActivityLogger.log_logout(db, current_user, http_request)

    response.delete_cookie(
        key=AuthConstants.COOKIE_NAME,
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,
        samesite=AuthConstants.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key="refresh_token",
        path=AuthConstants.COOKIE_PATH,
        httponly=True,
        secure=not settings.DEBUG,
        samesite=AuthConstants.COOKIE_SAMESITE,
    )

    return formatter.success(message="ログアウトしました")
