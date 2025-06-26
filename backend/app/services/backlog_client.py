import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class BacklogClient:
    """Backlog APIクライアント"""
    
    def __init__(self):
        self.base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/api/v2"
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """ユーザー情報を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/users/myself",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_issues(
        self, 
        user_id: int, 
        access_token: str,
        project_id: Optional[int] = None,
        status_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """ユーザーの課題一覧を取得"""
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
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/issues",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project_issues(
        self, 
        project_id: int, 
        access_token: str,
        status_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """プロジェクトの課題一覧を取得"""
        params = {
            "projectId[]": project_id,
            "count": limit,
            "offset": offset,
            "sort": "updated",
            "order": "desc"
        }
        
        if status_ids:
            params["statusId[]"] = status_ids
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/issues",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue_by_id(
        self,
        issue_id: int,
        access_token: str
    ) -> Dict[str, Any]:
        """課題の詳細情報を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/issues/{issue_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_project(
        self,
        project_id: int,
        access_token: str
    ) -> Dict[str, Any]:
        """プロジェクト情報を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_projects(
        self,
        access_token: str,
        archived: bool = False
    ) -> List[Dict[str, Any]]:
        """プロジェクト一覧を取得"""
        params = {"archived": archived}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue_statuses(
        self,
        project_id: int,
        access_token: str
    ) -> List[Dict[str, Any]]:
        """プロジェクトの課題ステータス一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/statuses",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue_comments(
        self,
        issue_id: int,
        access_token: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """課題のコメント一覧を取得"""
        params = {
            "count": limit,
            "offset": offset,
            "order": "asc"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/issues/{issue_id}/comments",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_activities(
        self,
        user_id: int,
        access_token: str,
        activity_type_ids: Optional[List[int]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
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
    
    async def get_priorities(self, access_token: str) -> List[Dict[str, Any]]:
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
    ) -> List[Dict[str, Any]]:
        """プロジェクトの課題種別一覧を取得"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/issueTypes",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()


backlog_client = BacklogClient()