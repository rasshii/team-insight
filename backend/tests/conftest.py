"""
pytest設定と共通フィクスチャ

このファイルはpytestによって自動的に読み込まれ、
全てのテストで使用できるフィクスチャを定義します。
"""
import pytest
from typing import Generator
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.core.security import create_access_token
from sqlalchemy import delete, text

@pytest.fixture(autouse=True)  # type: ignore
def clean_database():
    """各テストの前後でデータベースをクリーンアップとRBACセットアップ"""
    from app.models.rbac import Role, Permission
    from app.core.permissions import RoleType
    
    db = SessionLocal()
    try:
        # テスト前にクリーンアップ
        # 外部キー制約の順序を考慮して削除
        db.execute(text("DELETE FROM team_insight.activity_logs"))
        db.execute(text("DELETE FROM team_insight.login_history"))
        db.execute(text("DELETE FROM team_insight.report_delivery_history"))
        db.execute(text("DELETE FROM team_insight.report_schedules"))
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.team_members"))
        db.execute(text("DELETE FROM team_insight.teams"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_roles"))
        db.execute(text("DELETE FROM team_insight.user_preferences"))
        db.execute(delete(Project))
        # 全ユーザーを削除 (テスト隔離のため)。本番の初期管理者保護はテスト対象外
        db.execute(delete(User))
        db.commit()

        # RBACの基本ロールをセットアップ
        roles_data = [
            {"name": RoleType.ADMIN.value, "description": "Admin", "is_system": True},
            {"name": RoleType.PROJECT_LEADER.value, "description": "Project Leader", "is_system": True},
            {"name": RoleType.MEMBER.value, "description": "Member", "is_system": True}
        ]
        
        for role_data in roles_data:
            existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not existing_role:
                role = Role(**role_data)
                db.add(role)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Cleanup/Setup error (before test): {e}")
    
    yield
    
    try:
        # テスト後にもクリーンアップ
        db.execute(text("DELETE FROM team_insight.activity_logs"))
        db.execute(text("DELETE FROM team_insight.login_history"))
        db.execute(text("DELETE FROM team_insight.report_delivery_history"))
        db.execute(text("DELETE FROM team_insight.report_schedules"))
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.team_members"))
        db.execute(text("DELETE FROM team_insight.teams"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_roles"))
        db.execute(text("DELETE FROM team_insight.user_preferences"))
        db.execute(delete(Project))
        # 全ユーザーを削除 (テスト隔離のため)。本番の初期管理者保護はテスト対象外
        db.execute(delete(User))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Cleanup error (after test): {e}")
    finally:
        db.close()

@pytest.fixture(scope="function")
def test_user():
    """
    テスト用ユーザーをDBに投入し、テスト後に削除するfixture
    """
    db = SessionLocal()
    user = User(
        email="test@example.com",
        full_name="テストユーザー",
        is_active=True,
        is_superuser=False,
        name="テストユーザー"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


# ========== 追加の便利なフィクスチャ ==========

@pytest.fixture
def auth_headers(test_user) -> dict:
    """認証ヘッダー（一般ユーザー用）"""
    # test_userを明示的にリフレッシュして最新のIDを取得
    db = SessionLocal()
    user = db.query(User).filter(User.email == test_user.email).first()
    access_token = create_access_token(data={"sub": str(user.id)})
    db.close()
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_cookies(test_user) -> dict:
    """認証Cookie（一般ユーザー用）"""
    # test_userのIDを直接使用（セッションをまたがないように）
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"auth_token": access_token}


@pytest.fixture
def test_superuser():
    """テスト用管理者ユーザー"""
    db = SessionLocal()
    user = User(
        email="admin@example.com",
        full_name="管理者",
        is_active=True,
        is_superuser=True,
        name="管理者"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def admin_headers(test_superuser) -> dict:
    """認証ヘッダー（管理者用）"""
    access_token = create_access_token(data={"sub": str(test_superuser.id)})
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


# ========== 外部サービスのモック ==========

@pytest.fixture
def mock_redis():
    """Redisクライアントのモック"""
    with patch("app.core.redis_client.redis_client") as mock:
        mock.get = Mock(return_value=None)
        mock.set = Mock(return_value=True)
        mock.delete = Mock(return_value=True)
        mock.exists = Mock(return_value=False)
        yield mock


@pytest.fixture
def test_project(test_user):
    """テスト用プロジェクト"""
    # 新しいセッションで作業
    db = SessionLocal()
    
    # test_userを新しいセッションで取得
    user = db.query(User).filter(User.id == test_user.id).first()
    
    project = Project(
        name="Test Project",
        description="Test project description",
        project_key="TEST"
    )
    db.add(project)
    db.commit()
    
    # ユーザーをプロジェクトに追加
    project.members.append(user)
    db.commit()
    
    # IDを保存
    project_id = project.id
    
    yield project
    
    # クリーンアップ
    # 新しいセッションでクリーンアップ
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.members.clear()
        db.commit()
        db.delete(project)
        db.commit()
    
    db.close()


# ========== サンプルデータ ==========

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
