"""
組織メンバーシップリポジトリ (Phase 0)
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """組織メンバーシップリポジトリ"""

    def __init__(self, db: Session):
        super().__init__(OrganizationMember, db)

    def get_by_org_and_user(
        self, organization_id: int, user_id: int
    ) -> Optional[OrganizationMember]:
        return (
            self.db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
            .first()
        )

    def list_by_organization(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrganizationMember]:
        return (
            self.db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .filter(OrganizationMember.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_by_user(self, user_id: int) -> List[OrganizationMember]:
        return (
            self.db.query(OrganizationMember)
            .options(joinedload(OrganizationMember.organization))
            .filter(OrganizationMember.user_id == user_id)
            .all()
        )

    def count_admins(self, organization_id: int) -> int:
        """指定組織の ADMIN 数 (最後の ADMIN 削除を防ぐため)"""
        return (
            self.db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.role == "ADMIN",
            )
            .count()
        )
