"""
同期関連のスキーマ定義

Backlogデータ同期に関するリクエスト/レスポンスの
スキーマを定義します。
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class SyncStatus(str, Enum):
    """同期ステータス"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncResponse(BaseModel):
    """同期レスポンス"""
    status: SyncStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    """同期ステータスレスポンス"""
    connected: bool
    status: str
    message: str
    expires_at: Optional[datetime] = None
    last_project_sync: Optional[datetime] = None
    last_task_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectSyncResult(BaseModel):
    """プロジェクト同期結果"""
    success: bool
    created: int
    updated: int
    total: int
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class TaskSyncResult(BaseModel):
    """タスク同期結果"""
    success: bool
    created: int
    updated: int
    total: int
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True