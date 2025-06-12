import pytest
from app.db.session import SessionLocal
from app.models.user import User
from app.models.auth import OAuthToken, OAuthState
from datetime import datetime, timedelta

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
