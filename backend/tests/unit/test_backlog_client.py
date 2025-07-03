import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.backlog_client import BacklogClient
from app.core.exceptions import ExternalAPIException


class TestBacklogClient:
    """Backlog APIクライアントのテスト"""

    @pytest.fixture
    def client(self):
        return BacklogClient()

    @pytest.mark.asyncio
    async def test_get_user_issues_success(self, client):
        """ユーザーの課題一覧を正常に取得できること"""
        # モックデータの準備
        mock_issues = [
            {"id": 1, "summary": "タスク1", "status": {"name": "未対応"}},
            {"id": 2, "summary": "タスク2", "status": {"name": "処理中"}},
        ]

        # _make_requestメソッドをモック
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_issues

            # テスト実行
            result = await client.get_user_issues(
                user_id=123, access_token="test_token"
            )

            # 検証
            assert len(result) == 2
            assert result[0]["summary"] == "タスク1"
            assert result[1]["status"]["name"] == "処理中"
            
            # _make_requestが正しい引数で呼び出されたことを検証
            mock_make_request.assert_called_once_with(
                "GET",
                "/issues",
                "test_token",
                params={
                    "assigneeId[]": 123,
                    "count": 100,
                    "offset": 0,
                    "sort": "updated",
                    "order": "desc"
                }
            )

    @pytest.mark.asyncio
    async def test_get_user_issues_api_error(self, client):
        """エラー時に適切な例外が発生すること"""
        # _make_requestメソッドが例外をスローするようにモック
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_make_request:
            mock_make_request.side_effect = ExternalAPIException(
                service="Backlog",
                detail="APIリクエストが失敗しました: 404",
                data={"status_code": 404}
            )

            # 例外が発生することを検証
            with pytest.raises(ExternalAPIException) as exc_info:
                await client.get_user_issues(user_id=123, access_token="test_token")
            
            # 例外の内容を検証
            assert exc_info.value.detail == "APIリクエストが失敗しました: 404"
            assert exc_info.value.data["status_code"] == 404

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, client):
        """_make_requestメソッドがHTTPエラーを適切に処理すること"""
        with patch("app.services.backlog_client.httpx.AsyncClient") as mock_client_class:
            # モックレスポンスの作成
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Unauthorized", 
                request=MagicMock(), 
                response=mock_response
            )
            
            # AsyncClientのモック設定
            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.request = AsyncMock(return_value=mock_response)

            # 例外が発生することを検証
            with pytest.raises(ExternalAPIException) as exc_info:
                await client._make_request("GET", "/test", "invalid_token")
            
            # 例外の内容を検証
            assert "401" in exc_info.value.detail
            assert exc_info.value.data["status_code"] == 401

    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """_make_requestメソッドがネットワークエラーを適切に処理すること"""
        with patch("app.services.backlog_client.httpx.AsyncClient") as mock_client_class:
            # AsyncClientのモック設定
            mock_client_instance = MagicMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.request = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )

            # 例外が発生することを検証
            with pytest.raises(ExternalAPIException) as exc_info:
                await client._make_request("GET", "/test", "test_token")
            
            # 例外の内容を検証
            assert "通信中にエラーが発生しました" in exc_info.value.detail
            assert exc_info.value.data["error_type"] == "RequestError"

    @pytest.mark.asyncio
    async def test_get_project_issues_with_filters(self, client):
        """フィルター付きでプロジェクトの課題を取得できること"""
        mock_issues = [{"id": 1, "summary": "フィルターされた課題"}]
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_issues

            # ステータスIDでフィルター
            result = await client.get_project_issues(
                project_id=456,
                access_token="test_token",
                status_ids=[1, 2, 3]
            )

            # 検証
            assert len(result) == 1
            mock_make_request.assert_called_once_with(
                "GET",
                "/issues",
                "test_token",
                params={
                    "projectId[]": 456,
                    "count": 100,
                    "offset": 0,
                    "sort": "updated",
                    "order": "desc",
                    "statusId[]": [1, 2, 3]
                }
            )

    @pytest.mark.asyncio
    async def test_get_user_info(self, client):
        """ユーザー情報を正常に取得できること"""
        mock_user = {
            "id": 123,
            "userId": "testuser",
            "name": "テストユーザー",
            "mailAddress": "test@example.com"
        }
        
        with patch.object(client, "_make_request", new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_user

            result = await client.get_user_info("test_token")

            # 検証
            assert result["id"] == 123
            assert result["userId"] == "testuser"
            mock_make_request.assert_called_once_with("GET", "/users/myself", "test_token")