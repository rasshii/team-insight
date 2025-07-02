"""
同期スケジューラーサービス

APSchedulerを使用して定期的にBacklogデータの同期を実行します。
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.models.auth import OAuthToken
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.services.sync_service import sync_service
from app.core.config import settings
from app.core.token_refresh import token_refresh_service

logger = logging.getLogger(__name__)


class SyncSchedulerService:
    """同期スケジューラーサービス"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.job_prefix = "sync_schedule_"
        
    def start(self):
        """スケジューラーを開始"""
        try:
            # 定期同期ジョブを設定
            # 1. ユーザーインポート（日次 - 毎日午前2時）
            self.scheduler.add_job(
                self._sync_all_users,
                CronTrigger(hour=2, minute=0),
                id=f"{self.job_prefix}users_daily",
                replace_existing=True,
                name="Daily User Import"
            )
            
            # 2. プロジェクト同期（6時間ごと）
            self.scheduler.add_job(
                self._sync_all_projects,
                IntervalTrigger(hours=6),
                id=f"{self.job_prefix}projects",
                replace_existing=True,
                name="Project Sync Every 6 Hours"
            )
            
            # 3. タスク同期（12時間ごと）
            self.scheduler.add_job(
                self._sync_active_project_tasks,
                IntervalTrigger(hours=12),
                id=f"{self.job_prefix}tasks",
                replace_existing=True,
                name="Task Sync Every 12 Hours"
            )
            
            # 4. トークンリフレッシュチェック（1時間ごと）
            self.scheduler.add_job(
                self._refresh_expiring_tokens,
                IntervalTrigger(hours=1),
                id=f"{self.job_prefix}token_refresh",
                replace_existing=True,
                name="Token Refresh Check"
            )
            
            self.scheduler.start()
            logger.info("Sync scheduler started with jobs: users (daily), projects (6h), tasks (12h), tokens (1h)")
        except Exception as e:
            logger.error(f"Failed to start sync scheduler: {str(e)}")
    
    def stop(self):
        """スケジューラーを停止"""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Sync scheduler stopped")
        except Exception as e:
            logger.error(f"Failed to stop sync scheduler: {str(e)}")
    
    def add_custom_sync_job(
        self,
        job_id: str,
        sync_type: str,
        schedule: Dict[str, Any],
        user_id: Optional[int] = None
    ):
        """
        カスタム同期ジョブを追加
        
        Args:
            job_id: ジョブID
            sync_type: 同期タイプ（users, projects, tasks）
            schedule: スケジュール設定
            user_id: 特定ユーザーの同期の場合のユーザーID
        """
        # 実装は必要に応じて追加
        pass
    
    def remove_sync_job(self, job_id: str):
        """同期ジョブを削除"""
        try:
            self.scheduler.remove_job(f"{self.job_prefix}{job_id}")
            logger.info(f"Removed sync job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove sync job {job_id}: {str(e)}")
    
    def get_sync_jobs(self) -> List[Dict[str, Any]]:
        """アクティブな同期ジョブを取得"""
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith(self.job_prefix):
                jobs.append({
                    "id": job.id.replace(self.job_prefix, ""),
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        return jobs
    
    def _get_db(self) -> Session:
        """データベースセッションを取得"""
        return SessionLocal()
    
    def _get_system_user(self, db: Session) -> Optional[User]:
        """システム管理者ユーザーを取得"""
        # 最初の管理者ユーザーを取得
        admin_user = db.query(User).filter(
            User.is_admin == True,
            User.is_active == True
        ).first()
        return admin_user
    
    def _get_valid_token(self, user: User, db: Session) -> Optional[OAuthToken]:
        """有効なBacklogトークンを取得（自動リフレッシュ付き）"""
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not token:
            return None
        
        # トークンが期限切れまたは期限切れ間近の場合はリフレッシュ
        if token.is_expired() or token_refresh_service._should_refresh_token(token):
            try:
                refreshed_token = token_refresh_service.refresh_token_sync(
                    token, db, settings.BACKLOG_SPACE_KEY
                )
                if refreshed_token:
                    return refreshed_token
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user.id}: {str(e)}")
                return None
        
        return token
    
    async def _sync_all_users(self):
        """全ユーザーを同期（日次）"""
        db = self._get_db()
        try:
            admin_user = self._get_system_user(db)
            if not admin_user:
                logger.warning("No admin user found for scheduled user sync")
                return
            
            token = self._get_valid_token(admin_user, db)
            if not token:
                logger.warning(f"No valid token for admin user {admin_user.id}")
                return
            
            logger.info(f"Starting scheduled user import by admin {admin_user.id}")
            
            # ユーザーインポートを実行
            result = await sync_service.import_users_from_backlog(
                admin_user,
                token.access_token,
                db,
                mode="active_only",
                assign_default_role=True
            )
            
            logger.info(f"Scheduled user import completed: {result}")
            
        except Exception as e:
            logger.error(f"Failed in scheduled user sync: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    async def _sync_all_projects(self):
        """全プロジェクトを同期（6時間ごと）"""
        db = self._get_db()
        try:
            admin_user = self._get_system_user(db)
            if not admin_user:
                logger.warning("No admin user found for scheduled project sync")
                return
            
            token = self._get_valid_token(admin_user, db)
            if not token:
                logger.warning(f"No valid token for admin user {admin_user.id}")
                return
            
            logger.info(f"Starting scheduled project sync by admin {admin_user.id}")
            
            # プロジェクト同期を実行
            result = await sync_service.sync_all_projects(
                admin_user,
                token.access_token,
                db
            )
            
            logger.info(f"Scheduled project sync completed: {result}")
            
        except Exception as e:
            logger.error(f"Failed in scheduled project sync: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    async def _sync_active_project_tasks(self):
        """アクティブプロジェクトのタスクを同期（12時間ごと）"""
        db = self._get_db()
        try:
            admin_user = self._get_system_user(db)
            if not admin_user:
                logger.warning("No admin user found for scheduled task sync")
                return
            
            token = self._get_valid_token(admin_user, db)
            if not token:
                logger.warning(f"No valid token for admin user {admin_user.id}")
                return
            
            # アクティブなプロジェクトを取得
            from app.models.project import Project
            active_projects = db.query(Project).filter(
                Project.status == "active"
            ).limit(10).all()  # 負荷を考慮して上限を設定
            
            logger.info(f"Starting scheduled task sync for {len(active_projects)} active projects")
            
            for project in active_projects:
                try:
                    result = await sync_service.sync_project_tasks(
                        project,
                        token.access_token,
                        db,
                        admin_user
                    )
                    logger.info(f"Synced tasks for project {project.name}: {result}")
                except Exception as e:
                    logger.error(f"Failed to sync tasks for project {project.id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed in scheduled task sync: {str(e)}", exc_info=True)
        finally:
            db.close()
    
    def _refresh_expiring_tokens(self):
        """期限切れ間近のトークンをリフレッシュ（1時間ごと）"""
        db = self._get_db()
        try:
            # 1時間以内に期限切れになるトークンを検索
            expiry_threshold = datetime.utcnow() + timedelta(hours=1)
            
            expiring_tokens = db.query(OAuthToken).filter(
                OAuthToken.provider == "backlog",
                OAuthToken.expires_at <= expiry_threshold,
                OAuthToken.refresh_token.isnot(None)
            ).all()
            
            logger.info(f"Found {len(expiring_tokens)} tokens expiring within 1 hour")
            
            for token in expiring_tokens:
                try:
                    refreshed_token = token_refresh_service.refresh_token_sync(
                        token, db, settings.BACKLOG_SPACE_KEY
                    )
                    if refreshed_token:
                        logger.info(f"Successfully refreshed token for user {token.user_id}")
                    else:
                        logger.warning(f"Failed to refresh token for user {token.user_id}")
                except Exception as e:
                    logger.error(f"Error refreshing token for user {token.user_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed in token refresh check: {str(e)}", exc_info=True)
        finally:
            db.close()


# シングルトンインスタンス
sync_scheduler = SyncSchedulerService()