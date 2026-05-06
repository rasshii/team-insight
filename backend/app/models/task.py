"""
タスクモデル (Phase 0: マルチテナント対応)

すべてのタスクは organization_id で分離される。
"""

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel
import enum


class TaskStatus(str, enum.Enum):
    """タスクステータス"""

    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TaskPriority(int, enum.Enum):
    """タスク優先度"""

    HIGH = 2  # 高
    MEDIUM = 3  # 中
    LOW = 4  # 低


class Task(BaseModel):
    """タスクモデル"""

    __tablename__ = "tasks"
    __table_args__ = {"schema": "team_insight"}

    # マルチテナント分離キー
    organization_id = Column(
        Integer,
        ForeignKey("team_insight.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 関連ID
    project_id = Column(Integer, ForeignKey("team_insight.projects.id", ondelete="CASCADE"))
    assignee_id = Column(Integer, ForeignKey("team_insight.users.id", ondelete="SET NULL"))
    reporter_id = Column(Integer, ForeignKey("team_insight.users.id", ondelete="SET NULL"))

    # 基本情報
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.TODO)

    # 工数関連
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    # 日付関連
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)

    # リレーション
    organization = relationship("Organization")
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_tasks")

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title}>"
