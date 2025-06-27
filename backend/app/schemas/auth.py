"""
認証関連のPydanticスキーマ

このモジュールは、OAuth2.0認証フローで使用される
リクエスト/レスポンスのスキーマを定義します。
"""

from pydantic import BaseModel, Field, EmailStr, validator
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
    description: Optional[str] = Field(None, description="ロールの説明")

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
    backlog_id: Optional[int] = Field(None, description="BacklogのユーザーID")
    email: Optional[str] = Field(None, description="メールアドレス")
    name: str = Field(..., description="ユーザー名")
    user_id: Optional[str] = Field(None, description="BacklogのユーザーID（文字列）")
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


class SignupRequest(BaseModel):
    """
    サインアップリクエストスキーマ
    """
    email: EmailStr = Field(..., description="メールアドレス")
    password: str = Field(..., min_length=8, description="パスワード（8文字以上）")
    name: str = Field(..., min_length=1, max_length=100, description="表示名")
    
    @validator('password')
    def validate_password(cls, v):
        """パスワードの強度検証"""
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上必要です')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('パスワードには特殊文字を含める必要があります')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "name": "山田太郎"
            }
        }


class LoginRequest(BaseModel):
    """
    ログインリクエストスキーマ
    """
    email: EmailStr = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class SignupResponse(BaseModel):
    """
    サインアップレスポンススキーマ
    """
    message: str = Field(..., description="処理結果メッセージ")
    user: UserInfoResponse = Field(..., description="作成されたユーザー情報")
    requires_verification: bool = Field(default=True, description="メール確認が必要かどうか")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "アカウントが作成されました。メールアドレスの確認をお願いします。",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "name": "山田太郎",
                    "is_email_verified": False
                },
                "requires_verification": True
            }
        }
