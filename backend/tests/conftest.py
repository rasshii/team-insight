"""
pytest設定と共通フィクスチャ

このファイルはpytestによって自動的に読み込まれ、
全てのテストで使用できるフィクスチャを定義します。
"""
import pytest
from typing import Generator
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.db.base import Base  # Import base to ensure all models are loaded
from app.models.user import User
from app.models.auth import OAuthToken, OAuthState
from app.models.project import Project
from app.core.security import get_password_hash, create_access_token
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

@pytest.fixture(autouse=True)
def clean_database():
    """各テストの前後でデータベースをクリーンアップとRBACセットアップ"""
    from app.models.rbac import Role, Permission
    from app.core.permissions import RoleType
    
    db = SessionLocal()
    try:
        # テスト前にクリーンアップ
        # 外部キー制約の順序を考慮して削除
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.sync_histories"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_roles"))
        db.execute(delete(OAuthToken))
        db.execute(delete(OAuthState))
        db.execute(delete(Project))
        db.execute(delete(User).where(User.email.in_(["test@example.com", "admin@example.com", "projecttest@example.com"])))
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
        db.execute(text("DELETE FROM team_insight.tasks"))
        db.execute(text("DELETE FROM team_insight.sync_histories"))
        db.execute(text("DELETE FROM team_insight.project_members"))
        db.execute(text("DELETE FROM team_insight.user_roles"))
        db.execute(delete(OAuthToken))
        db.execute(delete(OAuthState))
        db.execute(delete(Project))
        db.execute(delete(User).where(User.email.in_(["test@example.com", "admin@example.com", "projecttest@example.com"])))
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
        hashed_password="dummy_hashed_password",
        full_name="テストユーザー",
        is_active=True,
        is_superuser=False,
        backlog_id=12345,
        user_id="test_user_id",
        name="テストユーザー"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture(scope="function")
def test_oauth_token(test_user):
    """
    テスト用OAuthTokenをDBに投入し、テスト後に削除するfixture
    """
    db = SessionLocal()
    token = OAuthToken(
        user_id=test_user.id,
        provider="backlog",
        access_token="dummy_access_token",
        refresh_token="dummy_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    yield token
    db.delete(token)
    db.commit()
    db.close()

@pytest.fixture(scope="function")
def test_oauth_state(test_user):
    """
    テスト用OAuthStateをDBに投入し、テスト後に削除するfixture
    """
    db = SessionLocal()
    state = OAuthState(
        state="test_state",
        user_id=test_user.id,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    yield state
    db.delete(state)
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
        hashed_password=get_password_hash("adminpassword123"),
        full_name="管理者",
        is_active=True,
        is_superuser=True,
        backlog_id=99999,
        user_id="admin_user_id",
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
def mock_backlog_client():
    """Backlog APIクライアントのモック"""
    with patch("app.services.backlog.BacklogClient") as mock:
        # デフォルトのレスポンスを設定
        mock.return_value.get_project.return_value = {
            "id": 1,
            "projectKey": "TEST",
            "name": "Test Project",
        }
        mock.return_value.get_issues.return_value = [
            {"id": 1, "summary": "Test Issue 1"},
            {"id": 2, "summary": "Test Issue 2"},
        ]
        yield mock


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
        backlog_id=1234,
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
        "backlog_project_id": "TEST-001",
        "is_active": True,
    }


@pytest.fixture
def sample_task_data():
    """サンプルタスクデータ"""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "assignee_id": 1,
        "due_date": datetime.utcnow() + timedelta(days=7),
        "priority": "medium",
        "status": "todo",
    }
