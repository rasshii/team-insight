"""
認証関連のPydanticスキーマ

このモジュールは、JWT 認証フローで使用されるリクエスト/レスポンスの
スキーマを定義します。Backlog OAuth 関連スキーマは Phase 6 で削除済み。
Phase 1 (ID/パスワード認証) で LoginRequest 等を追加する。
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class RoleResponse(BaseModel):
    """ロール情報のレスポンススキーマ"""

    id: int = Field(..., description="ロールID")
    name: str = Field(..., description="ロール名")
    description: Optional[str] = Field(None, description="ロールの説明")

    class Config:
        from_attributes = True


class UserRoleResponse(BaseModel):
    """ユーザーロール情報のレスポンススキーマ"""

    id: int = Field(..., description="ユーザーロールID")
    role_id: int = Field(..., description="ロールID")
    project_id: Optional[int] = Field(None, description="プロジェクトID（NULLの場合はグローバルロール）")
    role: RoleResponse = Field(..., description="ロール情報")

    class Config:
        from_attributes = True


class UserInfoResponse(BaseModel):
    """ユーザー情報のレスポンススキーマ"""

    id: int = Field(..., description="内部ユーザーID")
    email: Optional[str] = Field(None, description="メールアドレス")
    name: str = Field(..., description="ユーザー名")
    user_roles: List[UserRoleResponse] = Field(default_factory=list, description="ユーザーのロール一覧")
    is_active: bool = Field(True, description="アカウントの有効状態")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "山田太郎",
                "user_roles": [
                    {
                        "id": 1,
                        "role_id": 1,
                        "project_id": None,
                        "role": {"id": 1, "name": "ADMIN", "description": "システム管理者"},
                    }
                ],
                "is_active": True,
            }
        }


class TokenResponse(BaseModel):
    """トークンレスポンススキーマ"""

    access_token: str = Field(..., description="JWTアクセストークン")
    refresh_token: str = Field(..., description="JWTリフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    user: UserInfoResponse = Field(..., description="ユーザー情報")


class TokenRefreshResponse(BaseModel):
    """トークンリフレッシュレスポンススキーマ"""

    access_token: str = Field(..., description="新しいJWTアクセストークン")
    refresh_token: str = Field(..., description="新しいJWTリフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
