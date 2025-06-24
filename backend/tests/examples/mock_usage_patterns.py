"""
Team Insightプロジェクトでのモック使用例
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
from freezegun import freeze_time


class TestBacklogService:
    """Backlog APIサービスのテスト"""
    
    @patch('app.services.backlog.requests.get')
    def test_fetch_project_with_mock(self, mock_get):
        """✅ モック推奨: 外部APIは必ずモック"""
        # Backlog APIのレスポンスをモック
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "id": 1,
            "projectKey": "TEST",
            "name": "Test Project"
        }
        
        from app.services.backlog import BacklogService
        service = BacklogService()
        project = service.get_project("TEST")
        
        assert project["name"] == "Test Project"
        mock_get.assert_called_once_with(
            "https://api.backlog.com/api/v2/projects/TEST",
            headers={"Authorization": "Bearer token"}
        )
    
    @patch('app.services.backlog.BacklogClient')
    async def test_sync_issues_with_mock(self, mock_client):
        """✅ モック推奨: バッチ処理の外部API呼び出し"""
        # 複数の課題を返すモック
        mock_client.get_issues.return_value = [
            {"id": 1, "summary": "Issue 1"},
            {"id": 2, "summary": "Issue 2"},
        ]
        
        from app.services.sync import sync_backlog_issues
        result = await sync_backlog_issues(project_id=1)
        
        assert result["synced_count"] == 2
        mock_client.get_issues.assert_called_once()


class TestAuthService:
    """認証サービスのテスト"""
    
    @freeze_time("2024-01-01 12:00:00")
    def test_token_creation_with_fixed_time(self):
        """✅ モック推奨: 時間依存のテスト"""
        from app.core.security import create_access_token
        
        token = create_access_token({"sub": "user123"})
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        
        # 時間が固定されているので、正確な有効期限を検証可能
        expected_exp = datetime(2024, 1, 1, 12, 30).timestamp()
        assert decoded["exp"] == expected_exp
    
    def test_password_hashing_no_mock(self):
        """❌ モック非推奨: セキュリティ関連は実際の実装でテスト"""
        from app.core.security import get_password_hash, verify_password
        
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        # 実際のハッシュ化アルゴリズムでテスト
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False


class TestDatabaseOperations:
    """データベース操作のテスト"""
    
    @pytest.mark.asyncio
    async def test_user_creation_integration(self, test_db):
        """❌ モック非推奨: 統合テストでは実際のDBを使用"""
        from app.repositories.user import UserRepository
        
        repo = UserRepository()
        user = await repo.create(test_db, {
            "email": "test@example.com",
            "name": "Test User"
        })
        
        # 実際にDBに保存されたことを確認
        saved = await repo.get(test_db, user.id)
        assert saved.email == "test@example.com"
    
    @patch('app.repositories.user.UserRepository.get')
    async def test_user_service_unit(self, mock_get):
        """✅ モック推奨: サービス層の単体テスト"""
        # リポジトリ層をモック
        mock_get.return_value = Mock(
            id=1,
            email="test@example.com",
            is_active=True
        )
        
        from app.services.user import UserService
        service = UserService()
        user = await service.get_user_by_id(1)
        
        assert user.email == "test@example.com"
        mock_get.assert_called_once_with(ANY, 1)


class TestCacheOperations:
    """キャッシュ操作のテスト"""
    
    @patch('app.core.redis_client.redis_client')
    async def test_cache_service_with_mock(self, mock_redis):
        """✅ モック推奨: 単体テストではRedisをモック"""
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        from app.services.cache import CacheService
        service = CacheService()
        
        # キャッシュミス → データ取得 → キャッシュ保存
        result = await service.get_or_set("key", lambda: "value")
        
        assert result == "value"
        mock_redis.get.assert_called_once_with("key")
        mock_redis.set.assert_called_once()
    
    @pytest.mark.integration
    async def test_cache_integration(self, redis_client):
        """❌ モック非推奨: 統合テストでは実際のRedisを使用"""
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        assert value == "test_value"


class TestEmailService:
    """メール送信サービスのテスト"""
    
    @patch('app.services.email.send_email')
    async def test_send_notification_email(self, mock_send):
        """✅ モック必須: メール送信は必ずモック"""
        mock_send.return_value = True
        
        from app.services.notification import send_welcome_email
        result = await send_welcome_email("user@example.com")
        
        assert result is True
        mock_send.assert_called_once_with(
            to="user@example.com",
            subject="Welcome to Team Insight",
            body=ANY
        )


class TestFileOperations:
    """ファイル操作のテスト"""
    
    def test_config_loading_no_mock(self, tmp_path):
        """❌ モック非推奨: ファイルシステムはtmp_pathを使用"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value")
        
        from app.utils.config_loader import load_config
        config = load_config(str(config_file))
        
        assert config["key"] == "value"
    
    @patch('app.services.storage.S3Client')
    def test_s3_upload_with_mock(self, mock_s3):
        """✅ モック推奨: クラウドストレージはモック"""
        mock_s3.upload_file.return_value = "https://s3.example.com/file.pdf"
        
        from app.services.storage import upload_to_s3
        url = upload_to_s3("file.pdf", b"content")
        
        assert url == "https://s3.example.com/file.pdf"
        mock_s3.upload_file.assert_called_once()


# ========== モック使用の判断基準 ==========

def mock_decision_tree():
    """
    モックを使うかどうかの判断基準
    
    1. 外部サービス（API、メール、SMS）？
       → YES: 必ずモック
    
    2. データベース操作？
       → 単体テスト: モック推奨
       → 統合テスト: 実DBを使用
    
    3. 時間・ランダム値に依存？
       → YES: モック推奨（freeze_time等）
    
    4. ファイルシステム？
       → tmp_pathで十分ならモック不要
       → クラウドストレージならモック
    
    5. 高コストな操作（課金API等）？
       → YES: 必ずモック
    
    6. テストの実行速度が重要？
       → YES: モックを検討
    
    7. 実装の正確性が重要？
       → YES: モックを避ける
    """
    pass