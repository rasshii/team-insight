import httpx
from typing import List, Optional, AsyncContextManager, Union
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.exceptions import ExternalAPIException
from app.schemas.backlog_types import (
    BacklogUser,
    BacklogIssue,
    BacklogProject,
    BacklogProjectWithDetails
)
import logging

logger = logging.getLogger(__name__)


class BacklogClient:
    """Backlog APIクライアント
    
    Backlog API v2との通信を管理するクライアントクラス。
    HTTPクライアントの作成、ヘッダー設定、エラーハンドリングを統一化。
    """
    
    def __init__(self):
        self.base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/api/v2"
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    @asynccontextmanager
    async def _get_client(self, access_token: str) -> AsyncContextManager[httpx.AsyncClient]:
        """
        認証済みHTTPクライアントを取得
        
        Args:
            access_token: Backlog APIアクセストークン
            
        Yields:
            httpx.AsyncClient: 設定済みのHTTPクライアント
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers,
            follow_redirects=True
        ) as client:
            yield client
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        **kwargs
    ) -> Union[dict, list]:
        """
        APIリクエストを実行
        
        Args:
            method: HTTPメソッド（GET, POST, PUT, DELETE）
            endpoint: APIエンドポイント（base_urlからの相対パス）
            access_token: アクセストークン
            **kwargs: httpxリクエストの追加引数
            
        Returns:
            APIレスポンスのJSONデータ
            
        Raises:
            ExternalAPIException: APIリクエストが失敗した場合
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._get_client(access_token) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Backlog API HTTP error: {e.response.status_code} - {e.response.text}")
            logger.error(f"Request URL: {url}")
            logger.error(f"Request method: {method}")
            raise ExternalAPIException(
                service="Backlog",
                detail=f"APIリクエストが失敗しました: {e.response.status_code} - {e.response.text[:200]}",
                data={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text[:500],  # レスポンスの最初の500文字のみ
                    "url": url,
                    "method": method
                }
            )
        except httpx.RequestError as e:
            logger.error(f"Backlog API request error: {str(e)}")
            raise ExternalAPIException(
                service="Backlog",
                detail=f"APIとの通信中にエラーが発生しました: {str(e)}",
                data={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in Backlog API call: {str(e)}")
            raise ExternalAPIException(
                service="Backlog",
                detail="予期しないエラーが発生しました",
                data={"error_type": type(e).__name__, "error": str(e)}
            )
    
    async def get_user_info(self, access_token: str) -> dict:
        """ユーザー情報を取得
        
        Args:
            access_token: Backlog APIアクセストークン
            
        Returns:
            ユーザー情報のディクショナリ
        """
        return await self._make_request("GET", "/users/myself", access_token)
    
    async def get_user_by_id(self, user_id: Union[int, str], access_token: str) -> dict:
        """指定されたユーザーの詳細情報を取得
        
        Args:
            user_id: ユーザーID（数値）またはユーザーID（文字列）
            access_token: Backlog APIアクセストークン
            
        Returns:
            ユーザー情報のディクショナリ（mailAddressフィールドを含む）
        """
        return await self._make_request("GET", f"/users/{user_id}", access_token)
    
    async def get_user_issues(
        self, 
        user_id: int, 
        access_token: str,
        project_id: Optional[int] = None,
        status_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """ユーザーの課題一覧を取得
        
        Args:
            user_id: ユーザーID
            access_token: アクセストークン
            project_id: プロジェクトID（オプション）
            status_ids: ステータスIDのリスト（オプション）
            limit: 取得件数の上限
            offset: オフセット
            
        Returns:
            課題情報のリスト
        """
        params = {
            "assigneeId[]": user_id,
            "count": limit,
            "offset": offset,
            "sort": "updated",
            "order": "desc"
        }
        
        if project_id:
            params["projectId[]"] = project_id
        
        if status_ids:
            params["statusId[]"] = status_ids
        
        return await self._make_request("GET", "/issues", access_token, params=params)
    
    async def get_project_issues(
        self, 
        project_id: int, 
        access_token: str,
        status_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """プロジェクトの課題一覧を取得
        
        Args:
            project_id: プロジェクトID
            access_token: アクセストークン
            status_ids: ステータスIDのリスト（オプション）
            limit: 取得件数の上限
            offset: オフセット
            
        Returns:
            課題情報のリスト
        """
        params = {
            "projectId[]": project_id,
            "count": limit,
            "offset": offset,
            "sort": "updated",
            "order": "desc"
        }
        
        if status_ids:
            params["statusId[]"] = status_ids
        
        return await self._make_request("GET", "/issues", access_token, params=params)
    
    async def get_issue_by_id(
        self,
        issue_id: int,
        access_token: str
    ) -> dict:
        """課題の詳細情報を取得
        
        Args:
            issue_id: 課題ID
            access_token: アクセストークン
            
        Returns:
            課題の詳細情報
        """
        return await self._make_request("GET", f"/issues/{issue_id}", access_token)
    
    async def get_project(
        self,
        project_id: int,
        access_token: str
    ) -> dict:
        """プロジェクト情報を取得
        
        Args:
            project_id: プロジェクトID
            access_token: アクセストークン
            
        Returns:
            プロジェクト情報
        """
        return await self._make_request("GET", f"/projects/{project_id}", access_token)
    
    async def get_projects(
        self,
        access_token: str,
        archived: bool = False
    ) -> List[dict]:
        """プロジェクト一覧を取得
        
        Args:
            access_token: アクセストークン
            archived: アーカイブ済みプロジェクトを含むか
            
        Returns:
            プロジェクト情報のリスト
        """
        params = {"archived": archived}
        logger.info(f"Getting projects from Backlog API: {self.base_url}/projects")
        result = await self._make_request("GET", "/projects", access_token, params=params)
        logger.info(f"Backlog API returned {len(result) if isinstance(result, list) else 'non-list'} projects")
        if isinstance(result, list) and len(result) > 0:
            logger.info(f"First project example: {result[0].get('projectKey', 'N/A')} - {result[0].get('name', 'N/A')}")
        return result
    
    async def get_issue_statuses(
        self,
        project_id: int,
        access_token: str
    ) -> List[dict]:
        """プロジェクトの課題ステータス一覧を取得
        
        Args:
            project_id: プロジェクトID
            access_token: アクセストークン
            
        Returns:
            ステータス情報のリスト
        """
        return await self._make_request("GET", f"/projects/{project_id}/statuses", access_token)
    
    async def get_issue_comments(
        self,
        issue_id: int,
        access_token: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """課題のコメント一覧を取得
        
        Args:
            issue_id: 課題ID
            access_token: アクセストークン
            limit: 取得件数の上限
            offset: オフセット
            
        Returns:
            コメント情報のリスト
        """
        params = {
            "count": limit,
            "offset": offset,
            "order": "asc"
        }
        
        return await self._make_request("GET", f"/issues/{issue_id}/comments", access_token, params=params)
    
    async def get_user_activities(
        self,
        user_id: int,
        access_token: str,
        activity_type_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """ユーザーのアクティビティ一覧を取得"""
        params = {
            "userId[]": user_id,
            "count": limit,
            "offset": offset
        }
        
        if activity_type_ids:
            params["activityTypeId[]"] = activity_type_ids
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/space/activities",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_priorities(self, access_token: str) -> List[dict]:
        """優先度一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/priorities",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue_types(
        self,
        project_id: int,
        access_token: str
    ) -> List[dict]:
        """プロジェクトの課題種別一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/issueTypes",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()


    async def get_project_users(
        self,
        project_id: int,
        access_token: str
    ) -> List[dict]:
        """プロジェクトメンバー一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/users",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project_categories(
        self,
        project_id: int,
        access_token: str
    ) -> List[dict]:
        """プロジェクトのカテゴリ一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/categories",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project_milestones(
        self,
        project_id: int,
        access_token: str
    ) -> List[dict]:
        """プロジェクトのマイルストーン一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/versions",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project_statistics(
        self,
        project_id: int,
        access_token: str
    ) -> dict:
        """プロジェクトの統計情報を取得"""
        # 課題の統計情報を取得
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # オープンな課題数
            open_issues_response = await client.get(
                f"{self.base_url}/issues/count",
                params={
                    "projectId[]": project_id,
                    "statusId[]": [1, 2, 3]  # 未対応、処理中、処理済み
                },
                headers={"Authorization": f"Bearer {access_token}"}
            )
            open_issues_response.raise_for_status()
            open_count = open_issues_response.json()["count"]
            
            # クローズした課題数
            closed_issues_response = await client.get(
                f"{self.base_url}/issues/count",
                params={
                    "projectId[]": project_id,
                    "statusId[]": [4]  # 完了
                },
                headers={"Authorization": f"Bearer {access_token}"}
            )
            closed_issues_response.raise_for_status()
            closed_count = closed_issues_response.json()["count"]
            
            return {
                "open_issues": open_count,
                "closed_issues": closed_count,
                "total_issues": open_count + closed_count
            }


backlog_client = BacklogClient()