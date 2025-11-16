from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """Backlog OAuth経由でユーザーを作成するため、パスワードは不要"""

    pass


class UserUpdate(UserBase):
    """ユーザー情報の更新用スキーマ"""

    pass


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    """DB内のユーザー情報（Backlog OAuth専用のため、パスワードフィールドなし）"""

    pass
