"""
設定管理関連のPydanticスキーマ
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


class SettingBase(BaseModel):
    """設定基本スキーマ"""

    key: str = Field(..., description="設定キー")
    value: str = Field(..., description="設定値")
    group: str = Field(..., description="設定グループ（email, security, sync, system）")
    value_type: str = Field("string", description="値の型（string, integer, boolean, json）")
    description: Optional[str] = Field(None, description="設定の説明")
    is_sensitive: bool = Field(False, description="機密情報フラグ")


class SettingCreate(SettingBase):
    """設定作成スキーマ"""

    pass


class SettingUpdate(BaseModel):
    """設定更新スキーマ"""

    value: str = Field(..., description="設定値")


class Setting(SettingBase):
    """設定レスポンススキーマ"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingResponse(BaseModel):
    """設定レスポンス（機密情報はマスク）"""

    id: int
    key: str
    value: str  # is_sensitiveの場合はマスクされる
    group: str
    value_type: str
    description: Optional[str]
    is_sensitive: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettingsGroup(BaseModel):
    """設定グループスキーマ"""

    email: Dict[str, Any] = Field(default_factory=dict, description="メール設定")
    security: Dict[str, Any] = Field(default_factory=dict, description="セキュリティ設定")
    sync: Dict[str, Any] = Field(default_factory=dict, description="同期設定")
    system: Dict[str, Any] = Field(default_factory=dict, description="システム設定")


class EmailSettings(BaseModel):
    """メール設定"""

    email_from: str = Field(default="noreply@teaminsight.dev", description="送信元メールアドレス")
    email_from_name: str = Field(default="Team Insight", description="送信者名")


class SecuritySettings(BaseModel):
    """セキュリティ設定"""

    session_timeout: int = Field(default=60, description="セッションタイムアウト（分）")
    password_min_length: int = Field(default=8, description="パスワード最小文字数")
    login_attempt_limit: int = Field(default=5, description="ログイン失敗ロック回数")
    api_rate_limit: int = Field(default=100, description="APIレート制限（リクエスト/分）")
    token_expiry: int = Field(default=24, description="トークン有効期限（時間）")


class SyncSettings(BaseModel):
    """同期設定"""

    backlog_sync_interval: int = Field(default=60, description="Backlog同期間隔（分）")
    backlog_cache_timeout: int = Field(default=300, description="Backlogキャッシュタイムアウト（秒）")
    api_timeout: int = Field(default=30, description="APIタイムアウト（秒）")
    max_retry_count: int = Field(default=3, description="最大リトライ回数")


class SystemSettings(BaseModel):
    """システム設定"""

    log_level: str = Field(default="info", description="ログレベル")
    debug_mode: bool = Field(default=False, description="開発モード")
    maintenance_mode: bool = Field(default=False, description="メンテナンスモード")
    data_retention_days: int = Field(default=365, description="データ保持期間（日）")
    backup_frequency: str = Field(default="daily", description="バックアップ頻度")


class AllSettings(BaseModel):
    """全設定"""

    email: EmailSettings
    security: SecuritySettings
    sync: SyncSettings
    system: SystemSettings


class SettingsUpdateRequest(BaseModel):
    """設定更新リクエスト"""

    email: Optional[EmailSettings] = None
    security: Optional[SecuritySettings] = None
    sync: Optional[SyncSettings] = None
    system: Optional[SystemSettings] = None
