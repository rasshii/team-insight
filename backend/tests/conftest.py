"""
pytest設定と共通フィクスチャ

このファイルはpytestによって自動的に読み込まれ、
全てのテストで使用できるフィクスチャを定義します。
"""
import pytest
from typing import Generator
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.db.session import SessionLocal, get_db
from app.models.user import User
from app.models.auth import OAuthToken, OAuthState
from app.models.project import Project
from app.core.security import get_password_hash, create_access_token
from sqlalchemy import delete, text

@pytest.fixture(autouse=True)
def clean_database():
    """各テストの前後でデータベースをクリーンアップ"""
    db = SessionLocal()
    # テスト前にクリーンアップ
    # project_members から先に削除（外部キー制約のため）
    db.execute(text("DELETE FROM team_insight.project_members"))
    db.execute(delete(OAuthToken))
    db.execute(delete(OAuthState))
    db.execute(delete(Project))
    db.execute(delete(User).where(User.email.in_(["test@example.com", "admin@example.com"])))
    db.commit()
    yield
    # テスト後にもクリーンアップ
    db.execute(text("DELETE FROM team_insight.project_members"))
    db.execute(delete(OAuthToken))
    db.execute(delete(OAuthState))
    db.execute(delete(Project))
    db.execute(delete(User).where(User.email.in_(["test@example.com", "admin@example.com"])))
    db.commit()
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
    db = SessionLocal()
    # test_userを現在のセッションにマージ
    test_user = db.merge(test_user)
    
    project = Project(
        backlog_id=1234,
        name="Test Project",
        description="Test project description",
        project_key="TEST"
    )
    db.add(project)
    db.commit()
    
    # ユーザーをプロジェクトに追加
    project.members.append(test_user)
    db.commit()
    db.refresh(project)
    
    yield project
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
