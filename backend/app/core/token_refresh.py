"""
Backlogアクセストークンの自動更新ミドルウェア

このモジュールは、Backlog APIアクセス時にトークンの有効期限を確認し、
必要に応じて自動的にリフレッシュする機能を提供します。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.auth import OAuthToken
from app.models.user import User
from app.services.backlog_oauth import backlog_oauth_service
from app.core.exceptions import TokenExpiredException, AuthenticationException

logger = logging.getLogger(__name__)


class TokenRefreshService:
    """トークンリフレッシュサービス"""

    @staticmethod
    async def get_valid_token(user: User, db: Session) -> Optional[str]:
        """
        有効なBacklogアクセストークンを取得する
        必要に応じて自動的にリフレッシュを行う

        Args:
            user: ユーザーオブジェクト
            db: データベースセッション

        Returns:
            有効なアクセストークン、またはNone（トークンが存在しない場合）

        Raises:
            TokenExpiredException: リフレッシュトークンも期限切れの場合
        """
        # ユーザーのBacklogトークンを取得
        oauth_token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id, OAuthToken.provider == "backlog").first()

        if not oauth_token:
            logger.warning(f"User {user.id} has no Backlog token")
            return None

        # トークンの有効期限を確認（5分のバッファを持たせる）
        now = datetime.now(timezone.utc)
        expires_at = (
            oauth_token.expires_at.replace(tzinfo=timezone.utc)
            if oauth_token.expires_at.tzinfo is None
            else oauth_token.expires_at
        )

        if expires_at > now + timedelta(minutes=5):
            # トークンはまだ有効
            return oauth_token.access_token

        # トークンの更新が必要
        logger.info(f"Refreshing Backlog token for user {user.id}")

        try:
            # リフレッシュトークンを使用して新しいトークンを取得
            new_token_data = await backlog_oauth_service.refresh_access_token(oauth_token.refresh_token)

            # データベースのトークンを更新
            oauth_token.access_token = new_token_data["access_token"]
            oauth_token.refresh_token = new_token_data["refresh_token"]
            oauth_token.expires_at = new_token_data["expires_at"]
            oauth_token.updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Successfully refreshed Backlog token for user {user.id}")

            return oauth_token.access_token

        except Exception as e:
            logger.error(f"Failed to refresh Backlog token for user {user.id}: {str(e)}")

            # リフレッシュトークンも無効な場合
            raise TokenExpiredException("アクセストークンの有効期限が切れています。再度ログインしてください。")

    @staticmethod
    async def ensure_valid_token(user: User, db: Session) -> str:
        """
        有効なBacklogアクセストークンを確実に取得する
        トークンが存在しない場合は例外を発生させる

        Args:
            user: ユーザーオブジェクト
            db: データベースセッション

        Returns:
            有効なアクセストークン

        Raises:
            AuthenticationException: トークンが存在しない場合
            TokenExpiredException: トークンの更新に失敗した場合
        """
        token = await TokenRefreshService.get_valid_token(user, db)

        if not token:
            raise AuthenticationException("Backlogアクセストークンが見つかりません。Backlog連携を行ってください。")

        return token

    def _should_refresh_token(self, token: OAuthToken) -> bool:
        """
        トークンをリフレッシュすべきかどうかを判定

        Args:
            token: OAuthTokenオブジェクト

        Returns:
            リフレッシュが必要な場合True
        """
        if not token.expires_at:
            return False

        now = datetime.now(timezone.utc)
        expires_at = token.expires_at.replace(tzinfo=timezone.utc) if token.expires_at.tzinfo is None else token.expires_at

        # 5分前にリフレッシュ
        return expires_at <= now + timedelta(minutes=5)

    async def refresh_token(self, token: OAuthToken, db: Session, space_key: Optional[str] = None) -> Optional[OAuthToken]:
        """
        トークンをリフレッシュ

        Args:
            token: リフレッシュするトークン
            db: データベースセッション
            space_key: Backlogスペースキー（オプション）

        Returns:
            リフレッシュされたトークン、失敗時はNone
        """
        try:
            # リフレッシュトークンを使用して新しいトークンを取得
            new_token_data = await backlog_oauth_service.refresh_access_token(token.refresh_token, space_key=space_key)

            # データベースのトークンを更新
            token.access_token = new_token_data["access_token"]
            token.refresh_token = new_token_data["refresh_token"]
            token.expires_at = new_token_data["expires_at"]
            token.updated_at = datetime.utcnow()

            db.commit()
            logger.info(f"Successfully refreshed Backlog token for user {token.user_id}")

            return token

        except Exception as e:
            logger.error(f"Failed to refresh Backlog token: {str(e)}", exc_info=True)
            return None

    def refresh_token_sync(self, token: OAuthToken, db: Session, space_key: Optional[str] = None) -> Optional[OAuthToken]:
        """
        トークンをリフレッシュ（同期版）

        スケジューラーなど同期コンテキストから呼び出すための同期版メソッド

        Args:
            token: リフレッシュするトークン
            db: データベースセッション
            space_key: Backlogスペースキー（オプション）

        Returns:
            リフレッシュされたトークン、失敗時はNone
        """
        import asyncio

        try:
            # 現在のイベントループを取得、なければ新規作成
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 非同期メソッドを同期的に実行
            return loop.run_until_complete(self.refresh_token(token, db, space_key))
        except Exception as e:
            logger.error(f"Failed to refresh token synchronously: {str(e)}", exc_info=True)
            return None


# シングルトンインスタンス
token_refresh_service = TokenRefreshService()
