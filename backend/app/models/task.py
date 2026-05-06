from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Float, Text
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
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_tasks")

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"
