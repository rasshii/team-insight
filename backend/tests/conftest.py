"""
pytest 設定と共通フィクスチャ (Phase 0: organization_members ベース)

Phase 0 で旧 RBAC (user_roles / roles / role_permissions / permissions) を廃止し、
権限管理を users.is_system_admin + organization_members.role に統合した。
"""

from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import delete, text

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.models.project import Project
from app.models.user import User


@pytest.fixture(autouse=True)  # type: ignore
def clean_database():
    """各テストの前後でデータベースをクリーンアップ + default 組織を確保"""
    db = SessionLocal()
    try:
        # テスト前にクリーンアップ (FK 順序に注意)
        db.execute(text("DELETE FROM team_insight.activity_logs"))
        db.execute(text("DELETE FROM team_insight.login_history"))
        db.execute(text("DELETE FROM team_insight.report_delivery_history"))
        db.execute(text("DELETE FROM team_insight.report_schedules"))
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.team_members"))
        db.execute(text("DELETE FROM team_insight.teams"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_preferences"))
        db.execute(delete(Project))
        db.execute(text("DELETE FROM team_insight.organization_members"))
        db.execute(delete(User))
        db.commit()

        # default 組織を確保 (マイグレーションで作成済だが冪等性確保)
        existing = (
            db.query(Organization)
            .filter(Organization.slug == "default")
            .first()
        )
        if not existing:
            org = Organization(
                name="Default Organization",
                slug="default",
                fiscal_year_start_month=4,
                timezone="Asia/Tokyo",
                settings={},
                is_active=True,
            )
            db.add(org)
            db.commit()
    except Exception as e:  # pragma: no cover
        db.rollback()
        print(f"Cleanup/Setup error (before test): {e}")

    yield

    try:
        db.execute(text("DELETE FROM team_insight.activity_logs"))
        db.execute(text("DELETE FROM team_insight.login_history"))
        db.execute(text("DELETE FROM team_insight.report_delivery_history"))
        db.execute(text("DELETE FROM team_insight.report_schedules"))
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.team_members"))
        db.execute(text("DELETE FROM team_insight.teams"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_preferences"))
        db.execute(delete(Project))
        db.execute(text("DELETE FROM team_insight.organization_members"))
        db.execute(delete(User))
        db.commit()
    except Exception as e:  # pragma: no cover
        db.rollback()
        print(f"Cleanup error (after test): {e}")
    finally:
        db.close()


@pytest.fixture(scope="function")
def default_organization() -> Organization:
    """default 組織を返すフィクスチャ"""
    db = SessionLocal()
    try:
        org = (
            db.query(Organization)
            .filter(Organization.slug == "default")
            .first()
        )
        return org
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_user(default_organization: Organization):
    """default 組織に MEMBER として所属するテストユーザー"""
    db = SessionLocal()
    user = User(
        email="test@example.com",
        full_name="テストユーザー",
        is_active=True,
        is_superuser=False,
        is_system_admin=False,
        name="テストユーザー",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = OrganizationMember(
        organization_id=default_organization.id,
        user_id=user.id,
        role=OrganizationRole.MEMBER.value,
    )
    db.add(membership)
    db.commit()

    yield user

    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture(scope="function")
def test_superuser(default_organization: Organization):
    """default 組織に ADMIN として所属する System Admin"""
    db = SessionLocal()
    user = User(
        email="admin@example.com",
        full_name="管理者",
        is_active=True,
        is_superuser=True,
        is_system_admin=True,
        name="管理者",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = OrganizationMember(
        organization_id=default_organization.id,
        user_id=user.id,
        role=OrganizationRole.ADMIN.value,
    )
    db.add(membership)
    db.commit()

    yield user

    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def auth_headers(test_user: User, default_organization: Organization) -> dict:
    """認証ヘッダー (一般ユーザー用、active_org_id を含む JWT)"""
    access_token = create_access_token(
        test_user.id,
        active_org_id=default_organization.id,
        is_system_admin=False,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_cookies(test_user: User, default_organization: Organization) -> dict:
    """認証 Cookie (一般ユーザー用)"""
    access_token = create_access_token(
        test_user.id,
        active_org_id=default_organization.id,
        is_system_admin=False,
    )
    return {"auth_token": access_token}


@pytest.fixture
def admin_headers(test_superuser: User, default_organization: Organization) -> dict:
    """認証ヘッダー (System Admin 用)"""
    access_token = create_access_token(
        test_superuser.id,
        active_org_id=default_organization.id,
        is_system_admin=True,
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def db_session() -> Generator:
    """データベースセッション"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def mock_redis():
    """Redis クライアントのモック"""
    with patch("app.core.redis_client.redis_client") as mock:
        mock.get = Mock(return_value=None)
        mock.set = Mock(return_value=True)
        mock.delete = Mock(return_value=True)
        mock.exists = Mock(return_value=False)
        yield mock


@pytest.fixture
def test_project(test_user: User, default_organization: Organization):
    """テスト用プロジェクト (default 組織に紐づく)"""
    db = SessionLocal()
    user = db.query(User).filter(User.id == test_user.id).first()

    project = Project(
        organization_id=default_organization.id,
        name="Test Project",
        description="Test project description",
        project_key="TEST",
    )
    db.add(project)
    db.commit()
    project.members.append(user)
    db.commit()
    project_id = project.id

    yield project

    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.members.clear()
        db.commit()
        db.delete(project)
        db.commit()

    db.close()


@pytest.fixture
def sample_project_data():
    """サンプルプロジェクトデータ"""
    return {
        "name": "Test Project",
        "description": "This is a test project",
        "is_active": True,
    }


@pytest.fixture
def sample_task_data():
    """サンプルタスクデータ"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "assignee_id": 1,
        "due_date": datetime.now(timezone.utc) + timedelta(days=7),
        "priority": "medium",
        "status": "todo",
    }
