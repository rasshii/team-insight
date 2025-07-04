from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """タスクの基本スキーマ"""
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """タスク作成用スキーマ"""
    project_id: int
    assignee_id: Optional[int] = None


class TaskUpdate(BaseModel):
    """タスク更新用スキーマ"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    assignee_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class UserBrief(BaseModel):
    """ユーザー簡易情報"""
    id: int
    name: Optional[str]
    email: Optional[str]
    backlog_id: Optional[int]
    
    class Config:
        from_attributes = True


class ProjectBrief(BaseModel):
    """プロジェクト簡易情報"""
    id: int
    name: str
    project_key: str
    backlog_id: int
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """タスクレスポンス用スキーマ"""
    id: int
    backlog_id: int
    backlog_key: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: Optional[int]
    issue_type_id: Optional[int]
    issue_type_name: Optional[str]
    
    # 工数情報
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    
    # 日付情報
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    
    # その他の情報
    milestone_id: Optional[int]
    milestone_name: Optional[str]
    category_names: Optional[str]
    version_names: Optional[str]
    
    # タイムスタンプ
    created_at: datetime
    updated_at: datetime
    
    # リレーション
    project: Optional[ProjectBrief]
    assignee: Optional[UserBrief]
    reporter: Optional[UserBrief]
    
    class Config:
        from_attributes = True
        use_enum_values = False
    


class TaskListResponse(BaseModel):
    """タスク一覧レスポンス"""
    total: int
    limit: int
    offset: int
    tasks: List[TaskResponse]


class TaskFilters(BaseModel):
    """タスクフィルタ条件"""
    project_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[int] = None
    priority: Optional[int] = None
    search: Optional[str] = None