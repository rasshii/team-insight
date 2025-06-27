"""
Backlog OAuth2.0認証サービス

このモジュールは、Backlog APIのOAuth2.0認証フローを処理します。
認証コードの取得、アクセストークンの取得、トークンのリフレッシュなどの機能を提供します。
"""

import httpx
from typing import Dict, Optional
from urllib.parse import urlencode
import secrets
import base64
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.auth import OAuthToken
from app.db.session import get_db
from sqlalchemy.orm import Session


class BacklogOAuthService:
    """
    Backlog OAuth2.0認証を処理するサービスクラス

    このクラスは、Backlog APIのOAuth2.0認証フローに必要な
    すべての機能を提供します。
    """

    def __init__(self):
        """サービスの初期化"""
        self.client_id = settings.BACKLOG_CLIENT_ID
        self.client_secret = settings.BACKLOG_CLIENT_SECRET
        self.redirect_uri = settings.BACKLOG_REDIRECT_URI
        self.space_key = settings.BACKLOG_SPACE_KEY

        # BacklogのベースURL（スペースキーに基づいて構築）
        self.base_url = f"https://{self.space_key}.backlog.jp"

    def get_authorization_url(self, space_key: Optional[str] = None, state: Optional[str] = None) -> str:
        """
        認証URLを生成します

        Args:
            space_key: BacklogのスペースキーOptional）インスタンスのデフォルト値を使用
            state: CSRF攻撃を防ぐためのランダムな文字列（オプション）

        Returns:
            認証URL
        """
        if not state:
            # stateが提供されない場合は、セキュアなランダム文字列を生成
            state = secrets.token_urlsafe(32)

        # space_keyが指定されている場合は、そのspace_keyのURLを使用
        if space_key:
            base_url = f"https://{space_key}.backlog.jp"
        else:
            base_url = self.base_url

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        auth_url = f"{base_url}/OAuth2AccessRequest.action?{urlencode(params)}"
        return auth_url, state

    async def exchange_code_for_token(self, code: str, space_key: Optional[str] = None) -> Dict[str, any]:
        """
        認証コードをアクセストークンに交換します

        Args:
            code: Backlogから受け取った認証コード
            space_key: BacklogのスペースキーOptional）インスタンスのデフォルト値を使用

        Returns:
            アクセストークン、リフレッシュトークン、有効期限などを含む辞書

        Raises:
            HTTPException: トークンの取得に失敗した場合
        """
        # space_keyが指定されている場合は、そのspace_keyのURLを使用
        if space_key:
            base_url = f"https://{space_key}.backlog.jp"
        else:
            base_url = self.base_url
            
        token_url = f"{base_url}/api/v2/oauth2/token"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise Exception(f"トークンの取得に失敗しました: {response.text}")

            token_data = response.json()

            # トークンの有効期限を計算
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_type": token_data["token_type"],
                "expires_in": token_data["expires_in"],
                "expires_at": expires_at,
            }

    async def refresh_access_token(self, refresh_token: str, space_key: Optional[str] = None) -> Dict[str, any]:
        """
        リフレッシュトークンを使用してアクセストークンを更新します

        Args:
            refresh_token: 保存されているリフレッシュトークン
            space_key: BacklogのスペースキーOptional）インスタンスのデフォルト値を使用

        Returns:
            新しいアクセストークン、リフレッシュトークン、有効期限などを含む辞書

        Raises:
            HTTPException: トークンの更新に失敗した場合
        """
        # space_keyが指定されている場合は、そのspace_keyのURLを使用
        if space_key:
            base_url = f"https://{space_key}.backlog.jp"
        else:
            base_url = self.base_url
            
        token_url = f"{base_url}/api/v2/oauth2/token"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise Exception(f"トークンの更新に失敗しました: {response.text}")

            token_data = response.json()

            # トークンの有効期限を計算
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

            return {
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "token_type": token_data["token_type"],
                "expires_in": token_data["expires_in"],
                "expires_at": expires_at,
            }

    async def get_user_info(self, access_token: str, space_key: Optional[str] = None) -> Dict[str, any]:
        """
        アクセストークンを使用してユーザー情報を取得します

        Args:
            access_token: 有効なアクセストークン
            space_key: BacklogのスペースキーOptional）インスタンスのデフォルト値を使用

        Returns:
            Backlogユーザー情報を含む辞書

        Raises:
            HTTPException: ユーザー情報の取得に失敗した場合
        """
        # space_keyが指定されている場合は、そのspace_keyのURLを使用
        if space_key:
            base_url = f"https://{space_key}.backlog.jp"
        else:
            base_url = self.base_url
            
        user_url = f"{base_url}/api/v2/users/myself"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                user_url, headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise Exception(f"ユーザー情報の取得に失敗しました: {response.text}")

            return response.json()

    def save_token(
        self, db: Session, user_id: int, token_data: Dict[str, any], space_key: Optional[str] = None
    ) -> OAuthToken:
        """
        トークンをデータベースに保存します

        Args:
            db: データベースセッション
            user_id: ユーザーID
            token_data: トークン情報
            space_key: BacklogのスペースキーOptional）

        Returns:
            保存されたOAuthTokenオブジェクト
        """
        # 既存のトークンを確認
        existing_token = (
            db.query(OAuthToken)
            .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "backlog")
            .first()
        )

        if existing_token:
            # 既存のトークンを更新
            existing_token.access_token = token_data["access_token"]
            existing_token.refresh_token = token_data["refresh_token"]
            existing_token.expires_at = token_data["expires_at"]
            existing_token.updated_at = datetime.utcnow()
            if space_key:
                existing_token.backlog_space_key = space_key
            db.commit()
            return existing_token
        else:
            # 新しいトークンを作成
            new_token = OAuthToken(
                user_id=user_id,
                provider="backlog",
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                backlog_space_key=space_key if space_key else self.space_key,
            )
            db.add(new_token)
            db.commit()
            db.refresh(new_token)
            return new_token


# サービスのシングルトンインスタンス
backlog_oauth_service = BacklogOAuthService()
