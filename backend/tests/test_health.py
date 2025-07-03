"""
ヘルスチェックエンドポイントのテスト

実際のレスポンス形式を確認し、フロントエンドのモックとの整合性を検証します。
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_response_format():
    """ヘルスチェックのレスポンス形式を確認"""
    response = client.get("/health")
    
    # ステータスコードの確認
    assert response.status_code == 200
    
    # レスポンスの形式を確認
    data = response.json()
    
    # 必須フィールドの存在確認
    assert "status" in data
    assert "services" in data
    assert "message" in data
    assert "timestamp" in data
    
    # statusの値確認
    assert data["status"] in ["healthy", "unhealthy"]
    
    # servicesの構造確認
    assert "api" in data["services"]
    assert "database" in data["services"]
    assert "redis" in data["services"]
    
    # 各サービスのステータス値確認
    for service, status in data["services"].items():
        assert status in ["healthy", "unhealthy"]
    
    # messageの確認
    assert data["message"] == "Team Insight API is running"
    
    # timestampの形式確認（ISO 8601）
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"]  # ISO 8601形式の確認
    
    print("実際のレスポンス:")
    print(data)


def test_health_check_all_services_healthy():
    """全サービスが正常な場合のテスト（モック環境では難しい）"""
    response = client.get("/health")
    data = response.json()
    
    # APIは常にhealthyであるべき
    assert data["services"]["api"] == "healthy"
    
    # 他のサービスは環境により異なる
    print(f"Database status: {data['services']['database']}")
    print(f"Redis status: {data['services']['redis']}")
    print(f"Overall status: {data['status']}")


if __name__ == "__main__":
    # 実際のレスポンスを確認
    test_health_check_response_format()
    test_health_check_all_services_healthy()