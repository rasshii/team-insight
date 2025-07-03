from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class BacklogConnectionBase(BaseModel):
    """Backlog連携の基本スキーマ"""
    space_key: Optional[str] = Field(None, description="Backlogスペースキー")
    connection_type: Optional[Literal["oauth"]] = Field(None, description="連携方法")


class BacklogOAuthConnect(BaseModel):
    """OAuth連携のリクエストスキーマ"""
    pass  # OAuth連携は外部フローなので追加フィールド不要


class BacklogConnectionStatus(BacklogConnectionBase):
    """Backlog連携状態のレスポンススキーマ"""
    is_connected: bool = Field(..., description="連携済みかどうか")
    connected_at: Optional[datetime] = Field(None, description="連携日時")
    last_sync_at: Optional[datetime] = Field(None, description="最終同期日時")
    expires_at: Optional[datetime] = Field(None, description="OAuth トークンの有効期限")
    user_email: Optional[str] = Field(None, description="連携されたBacklogユーザーのメール")


class BacklogConnectionTest(BaseModel):
    """接続テストのレスポンススキーマ"""
    success: bool = Field(..., description="テスト成功フラグ")
    message: str = Field(..., description="テスト結果メッセージ")
    user_info: Optional[dict] = Field(None, description="接続されたユーザー情報")


class BacklogDisconnect(BaseModel):
    """連携解除のレスポンススキーマ"""
    success: bool = Field(..., description="解除成功フラグ")
    message: str = Field(..., description="解除結果メッセージ")


class BacklogSpaceKeyUpdate(BaseModel):
    """スペースキー更新のリクエストスキーマ"""
    space_key: str = Field(..., description="Backlogスペースキー", min_length=1, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "space_key": "example-space"
            }
        }