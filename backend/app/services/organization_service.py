"""
組織サービス (Phase 0)

System Admin / Org Admin の権限境界を踏まえた組織 CRUD と
組織メンバーシップ管理を提供する。
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.tenant import TenantContext
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.models.user import User
from app.repositories.organization_member_repository import (
    OrganizationMemberRepository,
)
from app.repositories.organization_repository import OrganizationRepository

logger = logging.getLogger(__name__)


class OrganizationService:
    """組織 / 組織メンバーシップに関するビジネスロジック"""

    # ----- 組織管理 (System Admin 用) -----

    def create(
        self,
        db: Session,
        *,
        name: str,
        slug: str,
        fiscal_year_start_month: int = 4,
        timezone_str: str = "Asia/Tokyo",
        settings_value: Optional[dict] = None,
    ) -> Organization:
        repo = OrganizationRepository(db)
        if repo.get_by_slug(slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"slug '{slug}' は既に使用されています",
            )

        org = Organization(
            name=name,
            slug=slug,
            fiscal_year_start_month=fiscal_year_start_month,
            timezone=timezone_str,
            settings=settings_value or {},
            is_active=True,
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info(f"Organization created: id={org.id}, slug={slug}")
        return org

    def update(
        self, db: Session, *, organization: Organization, fields: dict
    ) -> Organization:
        for key, value in fields.items():
            if value is None:
                continue
            if hasattr(organization, key):
                setattr(organization, key, value)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        return organization

    def soft_delete(self, db: Session, *, organization: Organization) -> Organization:
        organization.is_active = False
        organization.deleted_at = datetime.now(timezone.utc)
        db.add(organization)
        db.commit()
        db.refresh(organization)
        logger.info(f"Organization soft-deleted: id={organization.id}")
        return organization

    def list_all(self, db: Session, *, skip: int, limit: int) -> List[Organization]:
        return OrganizationRepository(db).list_all(skip=skip, limit=limit)

    def list_for_user(self, db: Session, *, user_id: int) -> List[Organization]:
        """ユーザーが所属する組織一覧 (organization_members 経由)"""
        return (
            db.query(Organization)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id == Organization.id,
            )
            .filter(OrganizationMember.user_id == user_id)
            .filter(Organization.deleted_at.is_(None))
            .all()
        )

    def get(self, db: Session, organization_id: int) -> Optional[Organization]:
        return (
            db.query(Organization)
            .filter(Organization.id == organization_id)
            .first()
        )

    # ----- メンバー管理 (Org Admin 用) -----

    def add_member(
        self,
        db: Session,
        *,
        organization_id: int,
        user_id: int,
        role: str = OrganizationRole.MEMBER.value,
    ) -> OrganizationMember:
        repo = OrganizationMemberRepository(db)
        existing = repo.get_by_org_and_user(organization_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="このユーザーは既に組織メンバーです",
            )

        membership = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    def update_member_role(
        self,
        db: Session,
        *,
        organization_id: int,
        user_id: int,
        new_role: str,
    ) -> OrganizationMember:
        repo = OrganizationMemberRepository(db)
        membership = repo.get_by_org_and_user(organization_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="メンバーが見つかりません",
            )

        # 最後の ADMIN を MEMBER 等にダウングレードする操作は防ぐ
        if membership.role == OrganizationRole.ADMIN.value and new_role != OrganizationRole.ADMIN.value:
            admin_count = repo.count_admins(organization_id)
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="組織の最後の ADMIN ロールを変更することはできません",
                )

        membership.role = new_role
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership

    def remove_member(
        self, db: Session, *, organization_id: int, user_id: int
    ) -> None:
        repo = OrganizationMemberRepository(db)
        membership = repo.get_by_org_and_user(organization_id, user_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="メンバーが見つかりません",
            )

        # 最後の ADMIN を削除する操作は防ぐ
        if membership.role == OrganizationRole.ADMIN.value:
            admin_count = repo.count_admins(organization_id)
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="組織の最後の ADMIN メンバーを削除することはできません",
                )

        db.delete(membership)
        db.commit()

    def list_members(
        self, db: Session, *, organization_id: int, skip: int, limit: int
    ) -> List[OrganizationMember]:
        return OrganizationMemberRepository(db).list_by_organization(
            organization_id, skip=skip, limit=limit
        )

    def list_user_memberships(
        self, db: Session, *, user_id: int
    ) -> List[OrganizationMember]:
        """ユーザーの組織メンバーシップ一覧 (組織情報込み)"""
        return OrganizationMemberRepository(db).list_by_user(user_id)


organization_service = OrganizationService()
