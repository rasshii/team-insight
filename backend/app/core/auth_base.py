"""
認証関連の基底クラスとユーティリティ (Phase 0: organization_members ベースに更新)

このモジュールは認証エンドポイントで共通的に使用される機能を提供する。
"""

from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


class AuthResponseBuilder:
    """認証レスポンスの構築を担当するクラス (Phase 0)"""

    @staticmethod
    def build_user_response(user: User) -> Dict[str, Any]:
        """
        ユーザー情報のレスポンスを構築

        Phase 0: user_roles の代わりに organization_memberships を返却する。
        """
        memberships = []
        if hasattr(user, "organization_memberships"):
            for membership in user.organization_memberships or []:
                memberships.append(
                    {
                        "organization_id": membership.organization_id,
                        "organization_name": membership.organization.name
                        if membership.organization
                        else None,
                        "organization_slug": membership.organization.slug
                        if membership.organization
                        else None,
                        "role": membership.role,
                    }
                )

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_system_admin": bool(getattr(user, "is_system_admin", False)),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "organizations": memberships,
        }

    @staticmethod
    def build_auth_response(
        user: User,
        access_token: str,
        refresh_token: str,
        active_org_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """認証成功時のレスポンスを構築"""
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "active_org_id": active_org_id,
            "user": AuthResponseBuilder.build_user_response(user),
        }


class CookieManager:
    """Cookie の設定を管理するクラス"""

    @staticmethod
    def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
        """認証用 Cookie を設定"""
        is_production = settings.ENVIRONMENT == "production"

        response.set_cookie(
            key="auth_token",
            value=access_token,
            httponly=True,
            secure=is_production,
            samesite="lax" if is_production else "none",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_production,
            samesite="lax" if is_production else "none",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/",
        )

    @staticmethod
    def clear_auth_cookies(response: Response) -> None:
        """認証用 Cookie をクリア"""
        response.delete_cookie(key="auth_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")


class TokenManager:
    """トークンの生成と管理を担当するクラス (Phase 0: active_org_id 対応)"""

    @staticmethod
    def generate_tokens(
        user: User, active_org_id: Optional[int] = None
    ) -> tuple[str, str, str]:
        """
        アクセストークンとリフレッシュトークンを生成

        Returns:
            (access_token, refresh_token, refresh_jti) のタプル。
            refresh_jti は失効リスト登録時に使用。
        """
        access_token = create_access_token(
            user.id,
            active_org_id=active_org_id,
            is_system_admin=bool(user.is_system_admin),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token, refresh_jti = create_refresh_token(
            user.id,
            active_org_id=active_org_id,
            is_system_admin=bool(user.is_system_admin),
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return access_token, refresh_token, refresh_jti


class AuthService:
    """認証関連の共通処理を提供するサービス (Phase 0)"""

    @staticmethod
    def get_user_with_memberships(user_id: int, db: Session) -> Optional[User]:
        """
        organization_memberships を eager load してユーザーを取得
        """
        return (
            db.query(User)
            .options(
                joinedload(User.organization_memberships).joinedload(
                    "organization"
                )
            )
            .filter(User.id == user_id)
            .first()
        )

    @staticmethod
    def validate_user_active(user: User) -> None:
        """
        ユーザーがアクティブかどうかを検証

        Raises:
            HTTPException: ユーザーが無効な場合
        """
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="アカウントが無効化されています",
            )

    @staticmethod
    def resolve_default_active_org(user: User) -> Optional[int]:
        """
        ログイン時に使うデフォルトの active_org_id を決定する

        現状は organization_memberships の最初の組織を返す。
        (将来的にユーザー設定の last_active_org_id を参照する拡張余地あり)
        """
        if not user.organization_memberships:
            return None
        return user.organization_memberships[0].organization_id
