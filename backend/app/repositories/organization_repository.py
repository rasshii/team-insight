"""
組織リポジトリ (Phase 0)
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.repositories.base_repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """組織リポジトリ"""

    def __init__(self, db: Session):
        super().__init__(Organization, db)

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.slug == slug).first()

    def get_active(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """deleted_at が NULL かつ is_active=True の組織一覧"""
        return (
            self.db.query(Organization)
            .filter(Organization.is_active.is_(True))
            .filter(Organization.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """ソフトデリート済を含む全組織 (System Admin 用)"""
        return self.db.query(Organization).offset(skip).limit(limit).all()
