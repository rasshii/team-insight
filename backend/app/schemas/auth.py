"""
認証関連のPydanticスキーマ

このモジュールは、OAuth2.0認証フローで使用される
リクエスト/レスポンスのスキーマを定義します。
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AuthorizationResponse(BaseModel):
    """
    認証URL生成のレスポンススキーマ
    """
    authorization_url: str = Field(..., description="Backlogの認証URL")
    state: str = Field(..., description="CSRF対策用のランダムな文字列")

    class Config:
        json_schema_extra = {
            "example": {
                "authorization_url": "https://example.backlog.jp/OAuth2AccessRequest.action?response_type=code&client_id=xxx&redirect_uri=xxx&state=xxx",
                "state": "random_state_string"
            }
        }


class CallbackRequest(BaseModel):
    """
    OAuth2.0コールバックのリクエストスキーマ
    """
    code: str = Field(..., description="Backlogから受け取った認証コード")
    state: str = Field(..., description="認証開始時に生成したstate")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "authorization_code_from_backlog",
                "state": "random_state_string"
            }
        }


class RoleResponse(BaseModel):
    """
    ロール情報のレスポンススキーマ
    """
    id: int = Field(..., description="ロールID")
    name: str = Field(..., description="ロール名")
    description: str = Field(..., description="ロールの説明")

    class Config:
        from_attributes = True


class UserRoleResponse(BaseModel):
    """
    ユーザーロール情報のレスポンススキーマ
    """
    id: int = Field(..., description="ユーザーロールID")
    role_id: int = Field(..., description="ロールID")
    project_id: Optional[int] = Field(None, description="プロジェクトID（NULLの場合はグローバルロール）")
    role: RoleResponse = Field(..., description="ロール情報")

    class Config:
        from_attributes = True


class UserInfoResponse(BaseModel):
    """
    ユーザー情報のレスポンススキーマ
    """
    id: int = Field(..., description="内部ユーザーID")
    backlog_id: int = Field(..., description="BacklogのユーザーID")
    email: Optional[str] = Field(None, description="メールアドレス")
    name: str = Field(..., description="ユーザー名")
    user_id: str = Field(..., description="BacklogのユーザーID（文字列）")
    is_email_verified: bool = Field(..., description="メールアドレス検証済みかどうか")
    user_roles: List[UserRoleResponse] = Field(default_factory=list, description="ユーザーのロール一覧")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "backlog_id": 12345,
                "email": "user@example.com",
                "name": "山田太郎",
                "user_id": "yamada",
                "is_email_verified": False,
                "user_roles": [
                    {
                        "id": 1,
                        "role_id": 1,
                        "project_id": None,
                        "role": {
                            "id": 1,
                            "name": "ADMIN",
                            "description": "システム管理者"
                        }
                    }
                ]
            }
        }


class TokenResponse(BaseModel):
    """
    トークンレスポンススキーマ
    """
    access_token: str = Field(..., description="アプリケーション用のJWTアクセストークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    user: UserInfoResponse = Field(..., description="ユーザー情報")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "backlog_id": 12345,
                    "email": "user@example.com",
                    "name": "山田太郎",
                    "user_id": "yamada"
                }
            }
        }


class BacklogTokenInfo(BaseModel):
    """
    Backlogトークン情報のスキーマ（内部使用）
    """
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "backlog_access_token",
                "refresh_token": "backlog_refresh_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": "2024-01-01T00:00:00"
            }
        }


class EmailVerificationRequest(BaseModel):
    """
    メール検証リクエストスキーマ
    """
    email: str = Field(..., description="検証用メールを送信するメールアドレス")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class EmailVerificationConfirmRequest(BaseModel):
    """
    メール検証確認リクエストスキーマ
    """
    token: str = Field(..., description="メール検証トークン")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "verification_token_string"
            }
        }


class EmailVerificationResponse(BaseModel):
    """
    メール検証レスポンススキーマ
    """
    message: str = Field(..., description="処理結果メッセージ")
    email: Optional[str] = Field(None, description="検証されたメールアドレス")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "検証メールを送信しました",
                "email": "user@example.com"
            }
        }
