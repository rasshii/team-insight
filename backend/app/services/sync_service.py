from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.backlog_client import backlog_client
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.core.exceptions import ExternalAPIException, DatabaseException
from app.core.token_refresh import token_refresh_service
from app.schemas.backlog_types import BacklogIssue
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
    
    def _create_sync_history(
        self,
        db: Session,
        user_id: int,
        sync_type: SyncType,
        target_id: Optional[int] = None,
        target_name: str = ""
    ) -> SyncHistory:
        """
        同期履歴を作成する共通メソッド
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            sync_type: 同期タイプ
            target_id: 対象ID（プロジェクトIDなど）
            target_name: 対象名称
            
        Returns:
            作成された同期履歴オブジェクト
        """
        sync_history = SyncHistory(
            user_id=user_id,
            sync_type=sync_type,
            status=SyncStatus.STARTED,
            target_id=target_id,
            target_name=target_name
        )
        db.add(sync_history)
        db.flush()
        return sync_history
    
    async def _sync_issues_common(
        self,
        issues: List[dict],
        sync_history: Optional[SyncHistory],
        db: Session,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        課題同期の共通処理
        
        Args:
            issues: 同期する課題のリスト
            sync_history: 同期履歴オブジェクト（Optional）
            db: データベースセッション
            project_id: プロジェクトID（課題作成時に指定）
            
        Returns:
            同期結果の辞書
        """
        created_count = 0
        updated_count = 0
        
        try:
            for issue_data in issues:
                task = await self._sync_issue(issue_data, db, project_id=project_id)
                if task.created_at == task.updated_at:
                    created_count += 1
                else:
                    updated_count += 1
            
            # 同期履歴を完了としてマーク
            if sync_history:
                sync_history.complete(
                    items_created=created_count,
                    items_updated=updated_count,
                    total_items=len(issues)
                )
            
            db.commit()
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(issues)
            }
        except Exception as e:
            logger.error(f"Failed to sync issues: {str(e)}")
            if sync_history:
                sync_history.fail(str(e))
            db.rollback()
            raise
    
    async def sync_user_tasks(
        self,
        user: User,
        access_token: str,
        db: Session,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        ユーザーのタスクを同期
        
        Args:
            user: 対象ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            project_id: プロジェクトID（指定時はそのプロジェクトのみ）
            
        Returns:
            同期結果の辞書
        """
        # 同期履歴を作成
        sync_history = self._create_sync_history(
            db=db,
            user_id=user.id,
            sync_type=SyncType.USER_TASKS,
            target_id=project_id,
            target_name=f"User {user.name} tasks"
        )
        
        try:
            # Backlogから課題を取得
            issues = await backlog_client.get_user_issues(
                user.backlog_id,
                access_token,
                project_id=project_id
            )
            
            # 共通処理で同期を実行
            return await self._sync_issues_common(issues, sync_history, db)
        except Exception as e:
            logger.error(f"Failed to sync user tasks: {str(e)}")
            raise
    
    async def sync_project_tasks(
        self,
        project: Project,
        access_token: str,
        db: Session,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        プロジェクトのタスクを同期
        
        Args:
            project: 対象プロジェクト
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            user: 同期を実行するユーザー（オプション）
            
        Returns:
            同期結果の辞書
        """
        # 同期履歴を作成（userが渡されない場合はNone）
        sync_history = None
        if user:
            sync_history = self._create_sync_history(
                db=db,
                user_id=user.id,
                sync_type=SyncType.PROJECT_TASKS,
                target_id=project.id,
                target_name=f"Project: {project.name}"
            )
            
        try:
            # Backlogから課題を取得
            issues = await backlog_client.get_project_issues(
                project.backlog_id,
                access_token
            )
            
            # 共通処理で同期を実行
            return await self._sync_issues_common(
                issues, 
                sync_history, 
                db, 
                project_id=project.id
            )
        except Exception as e:
            logger.error(f"Failed to sync project tasks: {str(e)}")
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
        issue_data: dict,
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
        except (ValueError, TypeError) as e:
            logger.warning(f"日付のパースに失敗しました: {date_str} - {str(e)}")
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


    async def sync_all_projects(
        self,
        user: User,
        access_token: str,
        db: Session
    ) -> Dict[str, Any]:
        """全プロジェクトを同期"""
        # 同期履歴を作成
        sync_history = SyncHistory(
            user_id=user.id,
            sync_type=SyncType.ALL_PROJECTS,
            status=SyncStatus.STARTED,
            target_name="All Projects"
        )
        db.add(sync_history)
        db.flush()
        
        try:
            # Backlogから全プロジェクトを取得
            projects_data = await backlog_client.get_projects(access_token)
            
            created_count = 0
            updated_count = 0
            
            for project_data in projects_data:
                project = await self._sync_project(project_data, db)
                if project.created_at == project.updated_at:
                    created_count += 1
                else:
                    updated_count += 1
                
                # プロジェクトメンバーも同期
                await self._sync_project_members(project, project_data, access_token, db)
            
            # 同期履歴を完了としてマーク
            sync_history.complete(
                items_created=created_count,
                items_updated=updated_count,
                total_items=len(projects_data)
            )
            
            db.commit()
            
            logger.info(f"Synced {len(projects_data)} projects for user {user.id}")
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(projects_data)
            }
        except Exception as e:
            logger.error(f"Failed to sync all projects: {str(e)}")
            sync_history.fail(str(e))
            db.rollback()
            raise
    
    async def _sync_project(
        self,
        project_data: Dict[str, Any],
        db: Session
    ) -> Project:
        """プロジェクトデータを同期（内部メソッド）"""
        # 既存のプロジェクトを検索
        project = db.query(Project).filter(
            Project.backlog_id == project_data["id"]
        ).first()
        
        if not project:
            project = Project(backlog_id=project_data["id"])
            db.add(project)
        
        # プロジェクト情報の更新
        project.name = project_data["name"]
        project.project_key = project_data["projectKey"]
        project.description = project_data.get("description", "")
        project.status = "active" if not project_data.get("archived") else "archived"
        
        db.flush()  # IDを取得するため
        return project
    
    async def _sync_project_members(
        self,
        project: Project,
        project_data: Dict[str, Any],
        access_token: str,
        db: Session
    ) -> None:
        """プロジェクトメンバーを同期"""
        try:
            # Backlogからプロジェクトメンバーを取得
            members_data = await backlog_client.get_project_users(
                project.backlog_id,
                access_token
            )
            
            # バルク操作でメンバーを更新
            # メンバーのbacklog_idを収集
            backlog_ids = [member["id"] for member in members_data]
            
            # 既存ユーザーを一括取得
            existing_users = db.query(User).filter(
                User.backlog_id.in_(backlog_ids)
            ).all()
            existing_user_map = {u.backlog_id: u for u in existing_users}
            
            # 新規ユーザーをバルク作成
            new_users = []
            all_users = []
            
            for member_data in members_data:
                if member_data["id"] in existing_user_map:
                    all_users.append(existing_user_map[member_data["id"]])
                else:
                    new_user = User(
                        backlog_id=member_data["id"],
                        user_id=member_data.get("userId"),
                        name=member_data["name"],
                        email=member_data.get("mailAddress"),
                        is_active=True
                    )
                    new_users.append(new_user)
                    all_users.append(new_user)
            
            # 新規ユーザーをバルク挿入
            if new_users:
                db.bulk_save_objects(new_users)
                db.flush()  # IDを取得
            
            # プロジェクトメンバーを更新
            project.members = all_users
            
            logger.info(f"Synced {len(members_data)} members for project {project.id}")
            
        except ExternalAPIException:
            # Backlog APIエラーは再raise（上位で適切に処理される）
            raise
        except SQLAlchemyError as e:
            logger.error(f"プロジェクトメンバー同期中のデータベースエラー: {str(e)}")
            # メンバー同期の失敗はプロジェクト同期全体を止めない
        except Exception as e:
            logger.error(f"プロジェクトメンバー同期中の予期しないエラー: {str(e)}", exc_info=True)
            # メンバー同期の失敗はプロジェクト同期全体を止めない
    
    def check_connection(self, user: User, db: Session) -> bool:
        """Backlog接続を確認"""
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        return token is not None and not token.is_expired()
    
    async def get_connection_status(
        self,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """接続ステータスを取得"""
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not token:
            return {
                "connected": False,
                "status": "no_token",
                "message": "Backlogアクセストークンが設定されていません"
            }
        
        # トークンが期限切れまたは期限切れ間近の場合はリフレッシュを試みる
        if token.is_expired() or token_refresh_service._should_refresh_token(token):
            logger.info(f"Token expired or about to expire for user {user.id}, attempting refresh")
            try:
                refreshed_token = await token_refresh_service.refresh_token(token, db)
                if refreshed_token:
                    token = refreshed_token
                    logger.info(f"Successfully refreshed token for user {user.id}")
                else:
                    logger.error(f"Failed to refresh token for user {user.id}")
                    return {
                        "connected": False,
                        "status": "expired",
                        "message": "アクセストークンの有効期限が切れており、リフレッシュに失敗しました",
                        "expires_at": token.expires_at
                    }
            except Exception as e:
                logger.error(f"Error refreshing token for user {user.id}: {str(e)}")
                return {
                    "connected": False,
                    "status": "expired",
                    "message": "アクセストークンの有効期限が切れており、リフレッシュに失敗しました",
                    "expires_at": token.expires_at
                }
        
        # 最後の同期情報を取得
        last_sync_project = db.query(Project.updated_at).order_by(
            Project.updated_at.desc()
        ).first()
        
        last_sync_task = db.query(Task.updated_at).order_by(
            Task.updated_at.desc()
        ).first()
        
        return {
            "connected": True,
            "status": "active",
            "message": "正常に接続されています",
            "expires_at": token.expires_at,
            "last_project_sync": last_sync_project[0] if last_sync_project else None,
            "last_task_sync": last_sync_task[0] if last_sync_task else None
        }


sync_service = SyncService()