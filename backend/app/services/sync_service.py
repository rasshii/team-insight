from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.backlog_client import backlog_client
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
import logging

logger = logging.getLogger(__name__)


class SyncService:
    """Backlogデータ同期サービス"""
    
    def __init__(self):
        self.status_mapping = {
            "未対応": TaskStatus.TODO,
            "処理中": TaskStatus.IN_PROGRESS,
            "処理済み": TaskStatus.RESOLVED,
            "完了": TaskStatus.CLOSED,
        }
    
    async def sync_user_tasks(
        self,
        user: User,
        access_token: str,
        db: Session,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """ユーザーのタスクを同期"""
        try:
            issues = await backlog_client.get_user_issues(
                user.backlog_id,
                access_token,
                project_id=project_id
            )
            
            created_count = 0
            updated_count = 0
            
            for issue_data in issues:
                task = await self._sync_issue(issue_data, db)
                if task.created_at == task.updated_at:
                    created_count += 1
                else:
                    updated_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(issues)
            }
        except Exception as e:
            logger.error(f"Failed to sync user tasks: {str(e)}")
            db.rollback()
            raise
    
    async def sync_project_tasks(
        self,
        project: Project,
        access_token: str,
        db: Session
    ) -> Dict[str, Any]:
        """プロジェクトのタスクを同期"""
        try:
            issues = await backlog_client.get_project_issues(
                project.backlog_id,
                access_token
            )
            
            created_count = 0
            updated_count = 0
            
            for issue_data in issues:
                task = await self._sync_issue(issue_data, db, project_id=project.id)
                if task.created_at == task.updated_at:
                    created_count += 1
                else:
                    updated_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(issues)
            }
        except Exception as e:
            logger.error(f"Failed to sync project tasks: {str(e)}")
            db.rollback()
            raise
    
    async def sync_single_issue(
        self,
        issue_id: int,
        access_token: str,
        db: Session
    ) -> Task:
        """単一の課題を同期"""
        try:
            issue_data = await backlog_client.get_issue_by_id(issue_id, access_token)
            task = await self._sync_issue(issue_data, db)
            db.commit()
            return task
        except Exception as e:
            logger.error(f"Failed to sync issue {issue_id}: {str(e)}")
            db.rollback()
            raise
    
    async def _sync_issue(
        self,
        issue_data: Dict[str, Any],
        db: Session,
        project_id: Optional[int] = None
    ) -> Task:
        """課題データを同期（内部メソッド）"""
        # 既存のタスクを検索
        task = db.query(Task).filter(
            Task.backlog_id == issue_data["id"]
        ).first()
        
        if not task:
            task = Task(backlog_id=issue_data["id"])
            db.add(task)
        
        # 基本情報の更新
        task.backlog_key = issue_data["issueKey"]
        task.title = issue_data["summary"]
        task.description = issue_data.get("description", "")
        
        # ステータスのマッピング
        status_name = issue_data["status"]["name"]
        task.status = self.status_mapping.get(status_name, TaskStatus.TODO)
        
        # 優先度
        if issue_data.get("priority"):
            task.priority = issue_data["priority"]["id"]
        
        # 課題種別
        if issue_data.get("issueType"):
            task.issue_type_id = issue_data["issueType"]["id"]
            task.issue_type_name = issue_data["issueType"]["name"]
        
        # プロジェクト
        if project_id:
            task.project_id = project_id
        elif issue_data.get("projectId"):
            # BacklogプロジェクトIDから内部プロジェクトIDを取得
            project = db.query(Project).filter(
                Project.backlog_id == issue_data["projectId"]
            ).first()
            if project:
                task.project_id = project.id
        
        # 担当者
        if issue_data.get("assignee"):
            assignee = self._get_or_create_user(
                issue_data["assignee"],
                db
            )
            task.assignee_id = assignee.id
        
        # 報告者
        if issue_data.get("createdUser"):
            reporter = self._get_or_create_user(
                issue_data["createdUser"],
                db
            )
            task.reporter_id = reporter.id
        
        # 工数
        task.estimated_hours = issue_data.get("estimatedHours")
        task.actual_hours = issue_data.get("actualHours")
        
        # 日付
        if issue_data.get("startDate"):
            task.start_date = self._parse_date(issue_data["startDate"])
        
        if issue_data.get("dueDate"):
            task.due_date = self._parse_date(issue_data["dueDate"])
        
        # 完了日（ステータスが完了の場合は更新日を使用）
        if task.status == TaskStatus.CLOSED and issue_data.get("updated"):
            task.completed_date = self._parse_date(issue_data["updated"])
        
        # マイルストーン
        if issue_data.get("milestone") and issue_data["milestone"]:
            milestone = issue_data["milestone"][0]  # 最初のマイルストーン
            task.milestone_id = milestone["id"]
            task.milestone_name = milestone["name"]
        
        # カテゴリー
        if issue_data.get("category"):
            categories = [cat["name"] for cat in issue_data["category"]]
            task.category_names = ",".join(categories)
        
        # バージョン
        if issue_data.get("versions"):
            versions = [ver["name"] for ver in issue_data["versions"]]
            task.version_names = ",".join(versions)
        
        return task
    
    def _get_or_create_user(
        self,
        user_data: Dict[str, Any],
        db: Session
    ) -> User:
        """ユーザーを取得または作成"""
        user = db.query(User).filter(
            User.backlog_id == user_data["id"]
        ).first()
        
        if not user:
            user = User(
                backlog_id=user_data["id"],
                user_id=user_data.get("userId"),
                name=user_data["name"],
                email=user_data.get("mailAddress"),
                is_active=True
            )
            db.add(user)
            db.flush()  # IDを取得するため
        
        return user
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """日付文字列をパース"""
        if not date_str:
            return None
        
        try:
            # Backlogの日付形式: "2023-12-25T10:30:00Z"
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
    
    async def get_sync_status(
        self,
        project_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """同期状況を取得"""
        total_tasks = db.query(Task).filter(
            Task.project_id == project_id
        ).count()
        
        status_counts = {}
        for status in TaskStatus:
            count = db.query(Task).filter(
                Task.project_id == project_id,
                Task.status == status
            ).count()
            status_counts[status.value] = count
        
        last_sync = db.query(Task.updated_at).filter(
            Task.project_id == project_id
        ).order_by(Task.updated_at.desc()).first()
        
        return {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "last_sync": last_sync[0] if last_sync else None
        }


sync_service = SyncService()