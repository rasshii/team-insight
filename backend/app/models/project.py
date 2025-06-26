# backend/app/models/project.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base_class import BaseModel

# 多対多の中間テーブル
project_members = Table(
    "project_members",
    BaseModel.metadata,
    Column("project_id", Integer, ForeignKey("team_insight.projects.id")),
    Column("user_id", Integer, ForeignKey("team_insight.users.id")),
    schema="team_insight",
)


class Project(BaseModel):
    """プロジェクトモデル"""

    __tablename__ = "projects"
    __table_args__ = {"schema": "team_insight"}

    backlog_id = Column(Integer, unique=True, nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    project_key = Column(String, unique=True, nullable=False)
    status = Column(String, default="active")

    # リレーション
    members = relationship("User", secondary=project_members, back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
