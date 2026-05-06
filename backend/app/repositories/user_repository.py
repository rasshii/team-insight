"""
ユーザーリポジトリ (Phase 0: organization_memberships ベースに更新)

旧 RBAC (user_roles / roles) を廃止し、organization_members.role を経由した
権限管理に統合した。N+1 対策として organization_memberships を joinedload する。
"""

from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """ユーザーリポジトリ"""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """メールアドレスでユーザーを検索"""
        return self.db.query(User).filter(User.email == email).first()

    def get_with_memberships(self, user_id: int) -> Optional[User]:
        """
        organization_memberships + organization を eager load して取得
        (Phase 0: 旧 get_with_roles の置き換え)
        """
        return (
            self.db.query(User)
            .options(
                joinedload(User.organization_memberships).joinedload(
                    OrganizationMember.organization
                )
            )
            .filter(User.id == user_id)
            .first()
        )

    def get_with_projects(self, user_id: int) -> Optional[User]:
        """プロジェクト情報を含めてユーザーを取得"""
        return (
            self.db.query(User)
            .options(joinedload(User.projects))
            .filter(User.id == user_id)
            .first()
        )

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """アクティブなユーザーのみを取得"""
        return (
            self.db.query(User)
            .filter(User.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """ユーザー検索 (name / full_name / email の部分一致)"""
        search_pattern = f"%{query}%"
        return (
            self.db.query(User)
            .filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_system_admins(self) -> List[User]:
        """
        System Admin ユーザーを取得 (Phase 0)

        is_system_admin = True または is_superuser = True (legacy)
        """
        return (
            self.db.query(User)
            .options(
                joinedload(User.organization_memberships).joinedload(
                    OrganizationMember.organization
                )
            )
            .filter(or_(User.is_system_admin.is_(True), User.is_superuser.is_(True)))
            .all()
        )

    def get_users_by_project(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """指定されたプロジェクトのメンバーを取得"""
        from app.models.project import Project

        return (
            self.db.query(User)
            .join(User.projects)
            .filter(Project.id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_project(self, project_id: int) -> int:
        """指定されたプロジェクトのメンバー数をカウント"""
        from sqlalchemy import func

        from app.models.project import Project

        return (
            self.db.query(func.count(User.id))
            .join(User.projects)
            .filter(Project.id == project_id)
            .scalar()
            or 0
        )

    def get_users_by_organization(
        self, organization_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """指定組織のメンバーを取得"""
        return (
            self.db.query(User)
            .join(User.organization_memberships)
            .filter(OrganizationMember.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
