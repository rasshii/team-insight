"""
認証関連の基底クラスとユーティリティ

このモジュールは認証エンドポイントで共通的に使用される
機能を提供し、コードの重複を削減します。
"""

from typing import Dict, Any, Optional
from datetime import timedelta
from fastapi import Response, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.core.query_optimizer import QueryBuilder


class AuthResponseBuilder:
    """認証レスポンスの構築を担当するクラス"""

    @staticmethod
    def build_user_response(user: User) -> Dict[str, Any]:
        """
        ユーザー情報のレスポンスを構築

        Args:
            user: ユーザーモデル

        Returns:
            ユーザー情報を含む辞書
        """
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "user_roles": (
                [
                    {"role": {"id": ur.role.id, "name": ur.role.name, "description": ur.role.description}}
                    for ur in user.user_roles
                ]
                if hasattr(user, "user_roles")
                else []
            ),
        }

    @staticmethod
    def build_auth_response(user: User, access_token: str, refresh_token: str) -> Dict[str, Any]:
        """
        認証成功時のレスポンスを構築

        Args:
            user: ユーザーモデル
            access_token: アクセストークン
            refresh_token: リフレッシュトークン

        Returns:
            認証情報を含む辞書
        """
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": AuthResponseBuilder.build_user_response(user),
        }


class CookieManager:
    """Cookieの設定を管理するクラス"""

    @staticmethod
    def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
        """
        認証用Cookieを設定

        Args:
            response: FastAPIレスポンスオブジェクト
            access_token: アクセストークン
            refresh_token: リフレッシュトークン
        """
        # 開発環境と本番環境で設定を切り替え
        is_production = settings.ENVIRONMENT == "production"

        # アクセストークンCookie
        response.set_cookie(
            key="auth_token",
            value=access_token,
            httponly=True,
            secure=is_production,
            samesite="lax" if is_production else "none",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/",
        )

        # リフレッシュトークンCookie
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
        """
        認証用Cookieをクリア

        Args:
            response: FastAPIレスポンスオブジェクト
        """
        response.delete_cookie(key="auth_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")


class TokenManager:
    """トークンの生成と管理を担当するクラス"""

    @staticmethod
    def generate_tokens(user_id: int) -> tuple[str, str]:
        """
        アクセストークンとリフレッシュトークンを生成

        Args:
            user_id: ユーザーID

        Returns:
            (access_token, refresh_token)のタプル
        """
        access_token = create_access_token(
            data={"sub": str(user_id)}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user_id)}, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        return access_token, refresh_token


class AuthService:
    """認証関連の共通処理を提供するサービス"""

    @staticmethod
    def get_user_with_roles(user_id: int, db: Session) -> Optional[User]:
        """
        ロール情報を含むユーザーを取得

        Args:
            user_id: ユーザーID
            db: データベースセッション

        Returns:
            ユーザーモデル（ロール情報含む）
        """
        query = db.query(User).filter(User.id == user_id)
        return QueryBuilder.with_user_roles(query).first()

    @staticmethod
    def validate_user_active(user: User) -> None:
        """
        ユーザーがアクティブかどうかを検証

        Args:
            user: ユーザーモデル

        Raises:
            HTTPException: ユーザーが無効な場合
        """
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="アカウントが無効化されています")
