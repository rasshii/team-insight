"""
ユーザーモデル (Phase 0: マルチテナント対応)

Phase 0 で旧 RBAC (user_roles / roles / role_permissions / permissions) を廃止し、
権限管理を以下の二本柱に一本化した:
- is_system_admin: System Admin フラグ (テナントバイパス用)
- organization_memberships.role: 組織内ロール (ADMIN / PROJECT_LEADER / MEMBER)
"""

from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}

    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_system_admin = Column(Boolean, nullable=False, default=False)

    # ユーザー設定
    timezone = Column(String(50), default="Asia/Tokyo")
    locale = Column(String(10), default="ja")
    date_format = Column(String(20), default="YYYY-MM-DD")

    # Relationships (Phase 0: 旧 user_roles を廃止し organization_memberships に統合)
    organization_memberships = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects = relationship(
        "Project", secondary="team_insight.project_members", back_populates="members"
    )
    report_schedules = relationship(
        "ReportSchedule", back_populates="user", cascade="all, delete-orphan"
    )
    team_memberships = relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    login_history = relationship(
        "LoginHistory", back_populates="user", cascade="all, delete-orphan"
    )
    activity_logs = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks = relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee"
    )
    reported_tasks = relationship(
        "Task", foreign_keys="Task.reporter_id", back_populates="reporter"
    )

    @property
    def is_admin(self) -> bool:
        """
        System Admin か (legacy alias for is_system_admin)

        Phase 0 で旧グローバル ADMIN ロールを廃止したため、is_admin は System Admin
        と同義となった。組織内 ADMIN かどうかを判定するには
        is_admin_in_organization(org_id) を使う。
        """
        return bool(self.is_system_admin)

    def get_role_in_organization(self, organization_id: int) -> Optional[str]:
        """指定組織での自分のロールを返す。所属していなければ None"""
        for membership in self.organization_memberships:
            if membership.organization_id == organization_id:
                return membership.role
        return None

    def is_admin_in_organization(self, organization_id: int) -> bool:
        """指定組織で ADMIN ロールを持つか"""
        return self.get_role_in_organization(organization_id) == "ADMIN"

    def is_member_of_organization(self, organization_id: int) -> bool:
        """指定組織のメンバーか (ロール問わず)"""
        return self.get_role_in_organization(organization_id) is not None
