# backend/tests/test_projects.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.project import Project
from app.core.security import create_access_token

# TestClientインスタンスをセッション単位で作成
@pytest.fixture
def client():
    return TestClient(app)


def test_get_projects_unauthenticated(client):
    """
    認証なしでプロジェクト一覧を取得しようとすると401エラー
    """
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    data = response.json()
    # The response might have a different structure, so let's check what it contains
    assert "error" in data or "detail" in data
    if "error" in data:
        assert "Not authenticated" in data["error"]["message"]
    else:
        assert data["detail"] == "Not authenticated"


def test_get_projects_empty(client, test_user: User, auth_cookies: dict):
    """
    プロジェクトがない場合は空のリストを返す
    """
    # TestClientインスタンスにcookieを設定
    client.cookies.set("auth_token", auth_cookies["auth_token"])
    
    response = client.get("/api/v1/projects")
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        print(f"Cookies: {client.cookies}")
    assert response.status_code == 200
    data = response.json()
    # API returns formatted response with data.projects
    assert "data" in data
    assert "projects" in data["data"]
    assert data["data"]["projects"] == []


