"""
統合同期サービス（後方互換性）

このモジュールは、既存のコードとの後方互換性を保つための統合サービスを提供します。
新しく分割されたサービス（user_sync_service、project_sync_service、task_sync_service）を
内部で使用し、既存のインターフェースを維持します。

使用例（既存コード）:
    from app.services.sync_service import sync_service

    # 既存のコードはそのまま動作します
    result = await sync_service.sync_user_tasks(user, token, db)
    result = await sync_service.sync_all_projects(user, token, db)

推奨される使い方（新規コード）:
    from app.services.sync import user_sync_service, project_sync_service, task_sync_service

    # 分割されたサービスを直接使用
    result = await user_sync_service.import_users_from_backlog(user, token, db)
    result = await project_sync_service.sync_all_projects(user, token, db)
    result = await task_sync_service.sync_user_tasks(user, token, db)

Note:
    - このクラスは既存のコードとの互換性のためのラッパーです
    - 新規コードでは、分割されたサービスを直接使用することを推奨します
    - 将来的に非推奨となる可能性があります
"""

from typing import Dict, Any, Optional, Literal
from sqlalchemy.orm import Session

from app.services.sync.user_sync_service import user_sync_service
from app.services.sync.project_sync_service import project_sync_service
from app.services.sync.task_sync_service import task_sync_service
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.models.task import Task
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class IntegratedSyncService:
    """
    統合同期サービス（後方互換性のためのラッパー）

    既存のSyncServiceと同じインターフェースを提供し、
    内部で分割されたサービスを呼び出します。

    このクラスは後方互換性のために存在し、既存のコードを変更せずに
    新しいサービス構造を利用できるようにします。

    Attributes:
        status_mapping: タスク同期サービスのステータスマッピングへの参照
    """

    def __init__(self):
        """
        統合同期サービスを初期化

        Note:
            - status_mappingはtask_sync_serviceから参照されます
        """
        # タスク同期サービスのステータスマッピングを参照
        self.status_mapping = task_sync_service.status_mapping

    # ========================================
    # タスク同期関連メソッド
    # ========================================

    async def sync_user_tasks(
        self, user: User, access_token: str, db: Session, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        ユーザーのタスクを同期

        内部でtask_sync_service.sync_user_tasks()を呼び出します。

        Args:
            user: 対象ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            project_id: プロジェクトID（指定時はそのプロジェクトのみ）

        Returns:
            同期結果の辞書
        """
        return await task_sync_service.sync_user_tasks(user=user, access_token=access_token, db=db, project_id=project_id)

    async def sync_project_tasks(
        self, project: Project, access_token: str, db: Session, user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        プロジェクトのタスクを同期

        内部でtask_sync_service.sync_project_tasks()を呼び出します。

        Args:
            project: 対象プロジェクト
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            user: 同期を実行するユーザー（オプション）

        Returns:
            同期結果の辞書
        """
        return await task_sync_service.sync_project_tasks(project=project, access_token=access_token, db=db, user=user)

    async def sync_single_issue(self, issue_id: int, access_token: str, db: Session) -> Task:
        """
        単一の課題を同期

        内部でtask_sync_service.sync_single_issue()を呼び出します。

        Args:
            issue_id: Backlog課題ID
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            同期されたタスクオブジェクト
        """
        return await task_sync_service.sync_single_issue(issue_id=issue_id, access_token=access_token, db=db)

    async def get_sync_status(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        同期状況を取得

        内部でtask_sync_service.get_sync_status()を呼び出します。

        Args:
            project_id: プロジェクトID
            db: データベースセッション

        Returns:
            同期状況の辞書
        """
        return await task_sync_service.get_sync_status(project_id=project_id, db=db)

    # ========================================
    # プロジェクト同期関連メソッド
    # ========================================

    async def sync_all_projects(self, user: User, access_token: str, db: Session) -> Dict[str, Any]:
        """
        全プロジェクトを同期

        内部でproject_sync_service.sync_all_projects()を呼び出します。

        Args:
            user: 実行ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            同期結果の辞書
        """
        return await project_sync_service.sync_all_projects(user=user, access_token=access_token, db=db)

    # ========================================
    # ユーザー同期関連メソッド
    # ========================================

    async def import_users_from_backlog(
        self,
        user: User,
        access_token: str,
        db: Session,
        mode: Literal["all", "active_only"] = "active_only",
        assign_default_role: bool = True,
    ) -> Dict[str, Any]:
        """
        Backlogから全プロジェクトのユーザーをインポート

        内部でuser_sync_service.import_users_from_backlog()を呼び出します。

        Args:
            user: 実行ユーザー（管理者権限が必要）
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            mode: インポートモード（"all" または "active_only"）
            assign_default_role: Trueの場合、新規ユーザーにMEMBERロールを自動付与

        Returns:
            インポート結果の辞書
        """
        return await user_sync_service.import_users_from_backlog(
            user=user, access_token=access_token, db=db, mode=mode, assign_default_role=assign_default_role
        )

    async def update_users_email_addresses(self, user: User, access_token: str, db: Session) -> Dict[str, Any]:
        """
        既存ユーザーのメールアドレスを更新

        内部でuser_sync_service.update_users_email_addresses()を呼び出します。

        Args:
            user: 実行ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            更新結果の辞書
        """
        return await user_sync_service.update_users_email_addresses(user=user, access_token=access_token, db=db)

    # ========================================
    # 接続状態確認メソッド
    # ========================================

    def check_connection(self, user: User, db: Session) -> bool:
        """
        Backlog接続を確認

        Args:
            user: 対象ユーザー
            db: データベースセッション

        Returns:
            接続が有効な場合True

        Note:
            - トークンの存在と有効期限を確認します
        """
        token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id, OAuthToken.provider == "backlog").first()

        return token is not None and not token.is_expired()

    async def get_connection_status(self, user: User, db: Session) -> Dict[str, Any]:
        """
        接続ステータスを取得

        Args:
            user: 対象ユーザー
            db: データベースセッション

        Returns:
            接続ステータスの辞書

        Note:
            - このメソッドは複雑なロジックを含むため、
              将来的に別のサービスに移動する可能性があります
        """
        from app.core.token_refresh import token_refresh_service
        from datetime import datetime

        token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id, OAuthToken.provider == "backlog").first()

        if not token:
            return {"connected": False, "status": "no_token", "message": "Backlogアクセストークンが設定されていません"}

        # トークンが期限切れまたは期限切れ間近の場合はリフレッシュを試みる
        if token.is_expired() or token_refresh_service._should_refresh_token(token):
            logger.info(f"トークンが期限切れまたは期限切れ間近: user_id={user.id}, " f"expires_at={token.expires_at}")

            try:
                # スペースキーを取得
                space_key = token.backlog_space_key or settings.BACKLOG_SPACE_KEY
                logger.info(f"リフレッシュに使用するスペースキー: {space_key}")

                # トークンをリフレッシュ
                refreshed_token = await token_refresh_service.refresh_token(token, db, space_key)

                if refreshed_token:
                    token = refreshed_token
                    logger.info(f"トークンのリフレッシュに成功: user_id={user.id}")
                else:
                    logger.error(f"トークンのリフレッシュに失敗: user_id={user.id}")
                    return {
                        "connected": False,
                        "status": "expired",
                        "message": "アクセストークンの有効期限が切れており、リフレッシュに失敗しました。再度ログインしてください。",
                        "expires_at": token.expires_at,
                    }
            except Exception as e:
                logger.error(f"トークンのリフレッシュ中にエラー: user_id={user.id}, error={str(e)}", exc_info=True)
                return {
                    "connected": False,
                    "status": "expired",
                    "message": f"アクセストークンの有効期限が切れており、リフレッシュに失敗しました: {str(e)}",
                    "expires_at": token.expires_at,
                }

        # 最後の同期情報を取得
        last_sync_project = db.query(Project.updated_at).order_by(Project.updated_at.desc()).first()

        last_sync_task = db.query(Task.updated_at).order_by(Task.updated_at.desc()).first()

        return {
            "connected": True,
            "status": "active",
            "message": "正常に接続されています",
            "expires_at": token.expires_at,
            "last_project_sync": last_sync_project[0] if last_sync_project else None,
            "last_task_sync": last_sync_task[0] if last_sync_task else None,
        }


# シングルトンインスタンス（後方互換性のため）
sync_service = IntegratedSyncService()
