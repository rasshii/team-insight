from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.backlog_client import backlog_client
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.models.rbac import Role, UserRole
from app.core.permissions import RoleType
from app.core.exceptions import ExternalAPIException, DatabaseException
from app.core.token_refresh import token_refresh_service
from app.schemas.backlog_types import BacklogIssue
from app.core.config import settings
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
        # BacklogのステータスIDも保存
        task.status_id = issue_data["status"]["id"]
        
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
        logger.info(f"Starting project sync for user {user.id}")
        
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
            logger.info(f"Fetching projects from Backlog for user {user.id}")
            logger.info(f"Using Backlog space key: {settings.BACKLOG_SPACE_KEY}")
            logger.info(f"Backlog API base URL: {backlog_client.base_url}")
            projects_data = await backlog_client.get_projects(access_token)
            logger.info(f"Received {len(projects_data)} projects from Backlog")
            
            created_count = 0
            updated_count = 0
            
            for project_data in projects_data:
                logger.debug(f"Syncing project: {project_data.get('projectKey')} - {project_data.get('name')}")
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
            
            # プロジェクトが更新されたらキャッシュを無効化
            from app.core.redis_client import redis_client
            try:
                # プロジェクト関連のキャッシュを削除
                deleted_count = await redis_client.delete_pattern("cache:http:*projects*")
                logger.info(f"Invalidated {deleted_count} project cache entries after sync")
            except Exception as e:
                logger.warning(f"Failed to invalidate project cache: {str(e)}")
                # キャッシュ削除の失敗は同期処理全体を止めない
            
            logger.info(f"Successfully synced {len(projects_data)} projects for user {user.id} (created: {created_count}, updated: {updated_count})")
            
            return {
                "success": True,
                "created": created_count,
                "updated": updated_count,
                "total": len(projects_data)
            }
        except Exception as e:
            logger.error(f"Failed to sync all projects for user {user.id}: {str(e)}", exc_info=True)
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
            
            # プロジェクトメンバーとして設定するユーザーリスト
            all_users = []
            
            for member_data in members_data:
                # ユーザーの詳細情報を取得（メールアドレスを含む）
                try:
                    user_id_str = member_data.get("userId") or str(member_data["id"])
                    detailed_member_data = await backlog_client.get_user_by_id(
                        user_id_str,
                        access_token
                    )
                    # 詳細情報で上書き
                    member_data.update(detailed_member_data)
                except Exception as e:
                    logger.debug(f"Failed to get detailed info for member {member_data.get('name', 'Unknown')}: {str(e)}")
                
                # 既存ユーザーを検索
                user = db.query(User).filter(
                    User.backlog_id == member_data["id"]
                ).first()
                
                if not user:
                    # 新規ユーザーを作成
                    user = User(
                        backlog_id=member_data["id"],
                        user_id=member_data.get("userId"),
                        name=member_data["name"],
                        email=member_data.get("mailAddress"),
                        is_active=True
                    )
                    db.add(user)
                    # 個別にflushして重複エラーを回避
                    try:
                        db.flush()
                    except SQLAlchemyError as e:
                        # 重複エラーの場合は既存ユーザーを取得
                        db.rollback()
                        user = db.query(User).filter(
                            User.backlog_id == member_data["id"]
                        ).first()
                        if not user:
                            logger.error(f"Failed to create or get user for backlog_id: {member_data['id']}")
                            continue
                else:
                    # 既存ユーザーの情報を更新
                    user.name = member_data["name"]
                    if member_data.get("mailAddress"):
                        user.email = member_data.get("mailAddress")
                    user.is_active = True
                
                all_users.append(user)
            
            # プロジェクトメンバーを更新
            project.members = all_users
            
            logger.info(f"Synced {len(all_users)} members for project {project.id} ({project.project_key})")
            logger.info(f"Project {project.project_key} member IDs: {[u.id for u in all_users]}")
            logger.info(f"Project {project.project_key} member names: {[u.name for u in all_users]}")
            
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
            logger.info(f"Token expires at: {token.expires_at}, current time: {datetime.utcnow()}")
            logger.info(f"Token has refresh_token: {bool(token.refresh_token)}")
            
            try:
                # スペースキーがあることを確認
                space_key = token.backlog_space_key or settings.BACKLOG_SPACE_KEY
                logger.info(f"Using space key for refresh: {space_key}")
                
                refreshed_token = await token_refresh_service.refresh_token(token, db, space_key)
                if refreshed_token:
                    token = refreshed_token
                    logger.info(f"Successfully refreshed token for user {user.id}")
                else:
                    logger.error(f"Failed to refresh token for user {user.id}")
                    return {
                        "connected": False,
                        "status": "expired",
                        "message": "アクセストークンの有効期限が切れており、リフレッシュに失敗しました。再度ログインしてください。",
                        "expires_at": token.expires_at
                    }
            except Exception as e:
                logger.error(f"Error refreshing token for user {user.id}: {str(e)}", exc_info=True)
                return {
                    "connected": False,
                    "status": "expired",
                    "message": f"アクセストークンの有効期限が切れており、リフレッシュに失敗しました: {str(e)}",
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
    
    async def import_users_from_backlog(
        self,
        user: User,
        access_token: str,
        db: Session,
        mode: Literal["all", "active_only"] = "active_only",
        assign_default_role: bool = True
    ) -> Dict[str, Any]:
        """
        Backlogから全プロジェクトのユーザーをインポート
        
        Args:
            user: 実行ユーザー（管理者権限が必要）
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            mode: インポートモード（"all" または "active_only"）
            assign_default_role: Trueの場合、新規ユーザーにMEMBERロールを自動付与
            
        Returns:
            インポート結果の辞書
        """
        logger.info(f"Starting Backlog user import for user {user.id} with mode: {mode}")
        
        # 同期履歴を作成
        sync_history = SyncHistory(
            user_id=user.id,
            sync_type=SyncType.ALL_USERS,
            status=SyncStatus.STARTED,
            target_name=f"Import Users ({mode})"
        )
        db.add(sync_history)
        db.flush()
        
        try:
            # まず全プロジェクトを取得
            projects_data = await backlog_client.get_projects(access_token)
            logger.info(f"Found {len(projects_data)} projects")
            
            created_users = 0
            updated_users = 0
            skipped_users = 0
            unique_users = {}  # backlog_id -> user_data のマップ
            
            # 各プロジェクトからユーザーを収集
            for project_data in projects_data:
                try:
                    # プロジェクトのユーザーを取得
                    project_users = await backlog_client.get_project_users(
                        project_data["id"],
                        access_token
                    )
                    
                    # ユニークなユーザーを収集（重複排除）
                    for user_data in project_users:
                        backlog_id = user_data["id"]
                        if backlog_id not in unique_users:
                            unique_users[backlog_id] = user_data
                            
                except Exception as e:
                    logger.warning(f"Failed to get users for project {project_data['name']}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(unique_users)} unique users across all projects")
            
            # MEMBERロールを取得（デフォルトロール付与用）
            member_role = None
            if assign_default_role:
                member_role = db.query(Role).filter(
                    Role.name == RoleType.MEMBER
                ).first()
                logger.info(f"assign_default_role={assign_default_role}, member_role found: {member_role is not None}")
            
            # ユーザーをインポート
            for backlog_id, user_data in unique_users.items():
                # ユーザーの詳細情報を取得（メールアドレスを含む）
                try:
                    # user_idまたはbacklog_idを使用してユーザー詳細を取得
                    user_id_str = user_data.get("userId") or str(backlog_id)
                    detailed_user_data = await backlog_client.get_user_by_id(
                        user_id_str,
                        access_token
                    )
                    # 詳細情報で上書き
                    user_data.update(detailed_user_data)
                    logger.debug(f"Got detailed info for user {user_data['name']}: email={user_data.get('mailAddress')}")
                except Exception as e:
                    logger.warning(f"Failed to get detailed info for user {user_data['name']} (ID: {backlog_id}): {str(e)}")
                    # 詳細情報の取得に失敗しても、基本情報でインポートを続行
                
                # 既存ユーザーを確認
                existing_user = db.query(User).filter(
                    User.backlog_id == backlog_id
                ).first()
                
                if existing_user:
                    # 既存ユーザーの情報を更新
                    existing_user.name = user_data["name"]
                    if user_data.get("mailAddress"):
                        existing_user.email = user_data.get("mailAddress")
                    
                    # active_onlyモードの場合、is_activeをTrueに設定
                    if mode == "active_only":
                        existing_user.is_active = True
                    
                    # 既存ユーザーでもロールを持っていない場合はデフォルトロールを付与
                    if member_role and assign_default_role:
                        # ユーザーがグローバルロールを持っているか確認
                        has_global_role = db.query(UserRole).filter(
                            UserRole.user_id == existing_user.id,
                            UserRole.project_id.is_(None)
                        ).first()
                        
                        logger.info(f"User {existing_user.name} (ID: {existing_user.id}): has_global_role={has_global_role is not None}, member_role_id={member_role.id if member_role else 'None'}")
                        
                        if not has_global_role:
                            user_role = UserRole(
                                user_id=existing_user.id,
                                role_id=member_role.id,
                                project_id=None  # グローバルロール
                            )
                            db.add(user_role)
                            logger.info(f"Added MEMBER role to user {existing_user.name} (ID: {existing_user.id})")
                    
                    updated_users += 1
                else:
                    # 新規ユーザーを作成
                    new_user = User(
                        backlog_id=backlog_id,
                        user_id=user_data.get("userId"),
                        name=user_data["name"],
                        email=user_data.get("mailAddress"),
                        is_active=True
                    )
                    db.add(new_user)
                    db.flush()  # IDを取得
                    
                    # デフォルトロールを付与
                    if member_role and assign_default_role:
                        user_role = UserRole(
                            user_id=new_user.id,
                            role_id=member_role.id,
                            project_id=None  # グローバルロール
                        )
                        db.add(user_role)
                    
                    created_users += 1
            
            # 同期履歴を完了としてマーク
            sync_history.complete(
                items_created=created_users,
                items_updated=updated_users,
                total_items=len(unique_users)
            )
            
            db.commit()
            
            logger.info(f"User import completed: created={created_users}, updated={updated_users}")
            
            return {
                "success": True,
                "created": created_users,
                "updated": updated_users,
                "skipped": skipped_users,
                "total": len(unique_users),
                "projects_scanned": len(projects_data),
                "default_role_assigned": assign_default_role and member_role is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to import users: {str(e)}", exc_info=True)
            sync_history.fail(str(e))
            db.rollback()
            raise


    async def update_users_email_addresses(
        self,
        user: User,
        access_token: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        既存ユーザーのメールアドレスを更新
        
        メールアドレスが未設定のユーザーに対して、
        Backlog APIから詳細情報を取得してメールアドレスを更新します。
        
        Args:
            user: 実行ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            
        Returns:
            更新結果の辞書
        """
        logger.info("Starting email address update for users without email")
        
        # メールアドレスが未設定のユーザーを取得
        users_without_email = db.query(User).filter(
            User.email.is_(None),
            User.backlog_id.isnot(None),
            User.user_id.isnot(None)
        ).all()
        
        logger.info(f"Found {len(users_without_email)} users without email address")
        
        updated_count = 0
        failed_count = 0
        
        for user_record in users_without_email:
            try:
                # ユーザーの詳細情報を取得
                user_id_str = user_record.user_id or str(user_record.backlog_id)
                detailed_user_data = await backlog_client.get_user_by_id(
                    user_id_str,
                    access_token
                )
                
                # メールアドレスを更新
                if detailed_user_data.get("mailAddress"):
                    user_record.email = detailed_user_data["mailAddress"]
                    updated_count += 1
                    logger.info(f"Updated email for user {user_record.name}: {user_record.email}")
                else:
                    logger.debug(f"No email address found for user {user_record.name}")
                    
            except Exception as e:
                logger.warning(f"Failed to update email for user {user_record.name}: {str(e)}")
                failed_count += 1
                continue
        
        db.commit()
        
        logger.info(f"Email address update completed: updated={updated_count}, failed={failed_count}")
        
        return {
            "success": True,
            "updated": updated_count,
            "failed": failed_count,
            "total_without_email": len(users_without_email)
        }


sync_service = SyncService()