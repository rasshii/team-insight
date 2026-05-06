"""
ユーザー管理関連の Pydantic スキーマ (Phase 0: organizations ベース)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.auth import OrganizationMembershipResponse


class UserBase(BaseModel):
    """ユーザー基本スキーマ"""

    email: Optional[str] = Field(None, description="メールアドレス")
    name: Optional[str] = Field(None, description="ユーザー名")
    is_active: bool = Field(True, description="アクティブ状態")


class UserCreate(UserBase):
    """ユーザー作成スキーマ"""


class UserUpdate(BaseModel):
    """ユーザー更新スキーマ"""

    email: Optional[str] = Field(None, description="メールアドレス")
    name: Optional[str] = Field(None, description="ユーザー名")
    is_active: Optional[bool] = Field(None, description="アクティブ状態")


class UserResponse(UserBase):
    """
    ユーザー情報レスポンス (Phase 0: organizations 配列を含む)
    """

    id: int = Field(..., description="ユーザー ID")
    is_system_admin: bool = Field(False, description="System Admin フラグ")
    organizations: List[OrganizationMembershipResponse] = Field(
        default_factory=list, description="ユーザーの所属組織一覧"
    )
    timezone: str = Field("Asia/Tokyo", description="タイムゾーン")
    locale: str = Field("ja", description="言語設定")
    date_format: str = Field("YYYY-MM-DD", description="日付フォーマット")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """ユーザー一覧レスポンス"""

    users: List[UserResponse] = Field(..., description="ユーザー一覧")
    total: int = Field(..., description="総ユーザー数")
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1 ページあたりの件数")


class UserInfo(BaseModel):
    """基本的なユーザー情報 (他のスキーマで使用)"""

    id: int = Field(..., description="ユーザー ID")
    name: Optional[str] = Field(None, description="ユーザー名")
    email: Optional[str] = Field(None, description="メールアドレス")

    model_config = ConfigDict(from_attributes=True)
