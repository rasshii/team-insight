"""
ユーザー管理関連のPydanticスキーマ
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.auth import UserRoleResponse, RoleResponse


class UserBase(BaseModel):
    """
    ユーザー基本スキーマ
    """
    email: Optional[str] = Field(None, description="メールアドレス")
    name: str = Field(..., description="ユーザー名")
    is_active: bool = Field(True, description="アクティブ状態")


class UserCreate(UserBase):
    """
    ユーザー作成スキーマ
    """
    pass


class UserUpdate(BaseModel):
    """
    ユーザー更新スキーマ
    """
    email: Optional[str] = Field(None, description="メールアドレス")
    name: Optional[str] = Field(None, description="ユーザー名")
    is_active: Optional[bool] = Field(None, description="アクティブ状態")


class UserResponse(UserBase):
    """
    ユーザー情報レスポンススキーマ
    """
    id: int = Field(..., description="ユーザーID")
    backlog_id: Optional[int] = Field(None, description="BacklogユーザーID")
    user_id: Optional[str] = Field(None, description="BacklogユーザーID（文字列）")
    user_roles: List[UserRoleResponse] = Field(default_factory=list, description="ユーザーのロール一覧")
    timezone: str = Field('Asia/Tokyo', description="タイムゾーン")
    locale: str = Field('ja', description="言語設定")
    date_format: str = Field('YYYY-MM-DD', description="日付フォーマット")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """
    ユーザー一覧レスポンススキーマ
    """
    users: List[UserResponse] = Field(..., description="ユーザー一覧")
    total: int = Field(..., description="総ユーザー数")
    page: int = Field(..., description="現在のページ")
    per_page: int = Field(..., description="1ページあたりの件数")


class UserRoleAssignment(BaseModel):
    """
    ユーザーロール割り当てスキーマ
    """
    role_id: int = Field(..., description="ロールID")
    project_id: Optional[int] = Field(None, description="プロジェクトID（NULLの場合はグローバルロール）")


class UserRoleAssignmentRequest(BaseModel):
    """
    ユーザーロール割り当てリクエストスキーマ
    """
    assignments: List[UserRoleAssignment] = Field(..., description="割り当てるロールのリスト")


class UserRoleRemovalRequest(BaseModel):
    """
    ユーザーロール削除リクエストスキーマ
    """
    user_role_ids: List[int] = Field(..., description="削除するユーザーロールIDのリスト")


class UserRoleUpdateRequest(BaseModel):
    """
    ユーザーロール更新リクエストスキーマ
    """
    user_role_id: int = Field(..., description="更新するユーザーロールID")
    role_id: int = Field(..., description="新しいロールID")


class UserInfo(BaseModel):
    """
    基本的なユーザー情報（他のスキーマで使用）
    """
    id: int = Field(..., description="ユーザーID")
    backlog_id: Optional[int] = Field(None, description="BacklogユーザーID")
    name: str = Field(..., description="ユーザー名")
    email: Optional[str] = Field(None, description="メールアドレス")
    
    class Config:
        from_attributes = True