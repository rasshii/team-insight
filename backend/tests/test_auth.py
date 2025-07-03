"""
認証関連のテスト

このモジュールは、認証関連の機能をテストします。
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

# テストクライアントの作成
client = TestClient(app)


@pytest.fixture
def mock_backlog_oauth():
    """BacklogOAuthServiceのモック"""
    with patch("app.api.v1.auth.backlog_oauth_service") as mock:
        yield mock


def test_get_authorization_url(mock_backlog_oauth):
    """認証URL取得のテスト"""
    # モックの設定
    import uuid
    unique_state = f"test_state_{uuid.uuid4().hex[:8]}"
    mock_backlog_oauth.get_authorization_url.return_value = ("https://example.backlog.com/oauth2/authorize", unique_state)

    # APIリクエスト
    response = client.get("/api/v1/auth/backlog/authorize")

    # レスポンスの検証
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    # stateは動的に生成されるため、authorization_urlの存在のみ確認
    assert "authorization_url" in response.json()
    assert "state" in response.json()
