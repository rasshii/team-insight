"""
ユーザー設定関連のPydanticスキーマ
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# UserPreferences
class UserPreferencesBase(BaseModel):
    """ユーザー設定基本スキーマ"""
    email_notifications: bool = Field(True, description="メール通知の有効/無効")
    report_frequency: str = Field("weekly", description="レポート配信頻度")
    notification_email: Optional[EmailStr] = Field(None, description="通知先メールアドレス")


class UserPreferencesCreate(UserPreferencesBase):
    """ユーザー設定作成スキーマ"""
    pass


class UserPreferencesUpdate(BaseModel):
    """ユーザー設定更新スキーマ"""
    email_notifications: Optional[bool] = None
    report_frequency: Optional[str] = None
    notification_email: Optional[EmailStr] = None


class UserPreferences(UserPreferencesBase):
    """ユーザー設定レスポンススキーマ"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# LoginHistory
class LoginHistoryBase(BaseModel):
    """ログイン履歴基本スキーマ"""
    ip_address: Optional[str] = Field(None, description="IPアドレス")
    user_agent: Optional[str] = Field(None, description="ユーザーエージェント")
    login_at: datetime = Field(..., description="ログイン日時")
    logout_at: Optional[datetime] = Field(None, description="ログアウト日時")
    session_id: Optional[str] = Field(None, description="セッションID")


class LoginHistory(LoginHistoryBase):
    """ログイン履歴レスポンススキーマ"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


# ActivityLog
class ActivityLogBase(BaseModel):
    """アクティビティログ基本スキーマ"""
    action: str = Field(..., description="アクション")
    resource_type: Optional[str] = Field(None, description="リソースタイプ")
    resource_id: Optional[int] = Field(None, description="リソースID")
    details: Optional[dict] = Field(None, description="詳細情報")
    ip_address: Optional[str] = Field(None, description="IPアドレス")
    created_at: datetime = Field(..., description="作成日時")


class ActivityLog(ActivityLogBase):
    """アクティビティログレスポンススキーマ"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


# User settings update
class UserSettingsUpdate(BaseModel):
    """ユーザー設定更新スキーマ"""
    name: Optional[str] = Field(None, description="表示名")
    timezone: Optional[str] = Field(None, description="タイムゾーン")
    locale: Optional[str] = Field(None, description="言語設定")
    date_format: Optional[str] = Field(None, description="日付フォーマット")
    email_notifications: Optional[bool] = Field(None, description="メール通知")
    report_frequency: Optional[str] = Field(None, description="レポート頻度")
    notification_email: Optional[EmailStr] = Field(None, description="通知先メール")


class UserSettings(BaseModel):
    """ユーザー設定レスポンススキーマ"""
    # 基本情報
    id: int
    email: Optional[str]
    name: Optional[str]
    backlog_id: Optional[int]
    is_active: bool
    
    # 設定
    timezone: str
    locale: str
    date_format: str
    
    # 通知設定
    preferences: Optional[UserPreferences] = None
    
    class Config:
        from_attributes = True


# Session info
class SessionInfo(BaseModel):
    """セッション情報スキーマ"""
    session_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_at: datetime
    is_current: bool = False


# Response schemas
class LoginHistoryListResponse(BaseModel):
    """ログイン履歴一覧レスポンス"""
    items: List[LoginHistory]
    total: int
    page: int
    page_size: int


class ActivityLogListResponse(BaseModel):
    """アクティビティログ一覧レスポンス"""
    items: List[ActivityLog]
    total: int
    page: int
    page_size: int