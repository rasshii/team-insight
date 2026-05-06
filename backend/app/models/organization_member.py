"""
組織メンバーシップモデル

User × Organization の M:M 関連を担い、組織内ロールを保持する。
権限管理は users.is_system_admin (テナントバイパス) と
organization_members.role (組織内ロール) の二本柱で行う。
"""

import enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.datetime_utils import utcnow
from app.db.base_class import BaseModel


class OrganizationRole(str, enum.Enum):
    """
    組織内ロール

    - ADMIN: 組織管理者 (メンバー招待・削除、ロール変更、組織設定変更)
    - PROJECT_LEADER: プロジェクトリーダー (プロジェクト管理、評価)
    - MEMBER: 一般メンバー (タスク操作、閲覧)
    """

    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    MEMBER = "MEMBER"


class OrganizationMember(BaseModel):
    """
    組織メンバーシップ

    1 ユーザーは複数組織に所属可能 (M:M)。
    組織切替 UI では JWT の active_org_id を更新する。
    """

    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_members_org_user"),
        CheckConstraint(
            "role IN ('ADMIN', 'PROJECT_LEADER', 'MEMBER')",
            name="ck_org_members_role",
        ),
        {"schema": "team_insight"},
    )

    organization_id = Column(
        Integer,
        ForeignKey("team_insight.organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        Integer,
        ForeignKey("team_insight.users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False, default=OrganizationRole.MEMBER.value)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organization_memberships")

    def __repr__(self) -> str:
        return (
            f"<OrganizationMember(org_id={self.organization_id}, "
            f"user_id={self.user_id}, role={self.role})>"
        )
