"""
プロジェクトモデル (Phase 0: マルチテナント対応)

すべてのプロジェクトは organization_id で分離される。
TenantScopedService を介したアクセスにより、別組織のプロジェクトは原則不可視。
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
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

    organization_id = Column(
        Integer,
        ForeignKey("team_insight.organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    description = Column(Text)
    project_key = Column(String, unique=True, nullable=False)
    status = Column(String, default="active")

    # リレーション
    organization = relationship("Organization")
    members = relationship("User", secondary=project_members, back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    report_schedules = relationship(
        "ReportSchedule", back_populates="project", cascade="all, delete-orphan"
    )
