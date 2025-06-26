# backend/tests/test_projects.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.project import Project
from app.core.security import create_access_token

client = TestClient(app)


def test_get_projects_unauthenticated():
    """
    認証なしでプロジェクト一覧を取得しようとすると401エラー
    """
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_projects_empty(test_user: User, auth_headers: dict):
    """
    プロジェクトがない場合は空のリストを返す
    """
    response = client.get("/api/v1/projects", headers=auth_headers)
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
    assert response.status_code == 200
    assert response.json() == []


def test_get_projects_with_data(
    test_user: User, test_project: Project, auth_headers: dict
):
    """
    プロジェクトがある場合はリストで返す
    """
    response = client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == test_project.name
    assert data[0]["description"] == test_project.description
    assert "created_at" in data[0]
