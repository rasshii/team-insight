"""
認証関連の Pydantic スキーマ (Phase 0: organization_memberships ベース)

Phase 6 で Backlog OAuth スキーマを削除済。
Phase 0 で旧 user_roles を廃止し、organizations 配列をユーザー情報に含めるよう変更。
Phase 1 (ID/パスワード認証) で LoginRequest 等を追加する。
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrganizationMembershipResponse(BaseModel):
    """ユーザーの組織所属情報 (organization_members.role を含む)"""

    organization_id: int = Field(..., description="組織 ID")
    organization_name: Optional[str] = Field(None, description="組織名")
    organization_slug: Optional[str] = Field(None, description="組織 slug")
    role: str = Field(..., description="組織内ロール (ADMIN / PROJECT_LEADER / MEMBER)")

    model_config = ConfigDict(from_attributes=True)


class UserInfoResponse(BaseModel):
    """ユーザー情報のレスポンス (Phase 0: organizations 配列を含む)"""

    id: int = Field(..., description="内部ユーザー ID")
    email: Optional[str] = Field(None, description="メールアドレス")
    name: Optional[str] = Field(None, description="ユーザー名")
    full_name: Optional[str] = Field(None, description="フルネーム")
    is_active: bool = Field(True, description="アカウントの有効状態")
    is_system_admin: bool = Field(False, description="System Admin フラグ")
    organizations: List[OrganizationMembershipResponse] = Field(
        default_factory=list, description="ユーザーの所属組織一覧"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "name": "山田太郎",
                "full_name": "山田 太郎",
                "is_active": True,
                "is_system_admin": False,
                "organizations": [
                    {
                        "organization_id": 1,
                        "organization_name": "Default Organization",
                        "organization_slug": "default",
                        "role": "ADMIN",
                    }
                ],
            }
        },
    )


class TokenResponse(BaseModel):
    """ログイン成功時のトークンレスポンス"""

    access_token: str = Field(..., description="JWT アクセストークン")
    refresh_token: str = Field(..., description="JWT リフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    active_org_id: Optional[int] = Field(
        None, description="ログイン後にデフォルト選択される組織 ID"
    )
    user: UserInfoResponse = Field(..., description="ユーザー情報")


class TokenRefreshResponse(BaseModel):
    """トークンリフレッシュレスポンス"""

    access_token: str = Field(..., description="新しい JWT アクセストークン")
    refresh_token: str = Field(..., description="新しい JWT リフレッシュトークン")
    token_type: str = Field(default="bearer", description="トークンタイプ")
    active_org_id: Optional[int] = Field(None, description="現在の active_org_id")


class SwitchOrganizationRequest(BaseModel):
    """組織切替リクエスト"""

    organization_id: int = Field(..., description="切り替え先の組織 ID")
