"""
タスク同期サービス

このモジュールは、Backlogからタスク（課題）情報を同期する機能を提供します。

主な機能:
- ユーザータスクの同期
- プロジェクトタスクの同期
- 単一タスクの同期
- タスクデータの変換（BacklogのIssue -> 内部のTask）
- 同期状況の取得

使用例:
    task_sync_service = TaskSyncService()
    result = await task_sync_service.sync_user_tasks(
        user=current_user,
        access_token=token,
        db=db
    )
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.backlog_client import backlog_client
from app.services.sync.base_sync_service import BaseSyncService
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.models.sync_history import SyncHistory, SyncType
import logging

logger = logging.getLogger(__name__)


class TaskSyncService(BaseSyncService):
    """
    タスク同期サービス

    Backlogからタスク（課題）情報を取得し、Team Insightのデータベースと同期します。
    ユーザー単位、プロジェクト単位、または単一タスクの同期をサポートします。

    継承:
        BaseSyncService: 共通機能（同期履歴管理、ユーザー作成など）を提供

    属性:
        status_mapping: BacklogのステータスをTaskStatusにマッピングする辞書
    """

    def __init__(self):
        """
        タスク同期サービスを初期化

        ステータスマッピング:
            - "未対応" -> TaskStatus.TODO
            - "処理中" -> TaskStatus.IN_PROGRESS
            - "処理済み" -> TaskStatus.RESOLVED
            - "完了" -> TaskStatus.CLOSED

        Note:
            - マッピングされていないステータスはTODOとして扱われます
        """
        self.status_mapping = {
            "未対応": TaskStatus.TODO,
            "処理中": TaskStatus.IN_PROGRESS,
            "処理済み": TaskStatus.RESOLVED,
            "完了": TaskStatus.CLOSED,
        }

    async def sync_user_tasks(
        self, user: User, access_token: str, db: Session, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        ユーザーのタスクを同期

        指定されたユーザーに割り当てられている全てのタスクをBacklogから取得し、
        ローカルデータベースと同期します。

        処理フロー:
            1. 同期履歴を作成（SyncType.USER_TASKS）
            2. Backlogからユーザーの課題を取得
            3. 各課題をタスクとして同期
            4. 同期履歴を完了としてマーク
            5. 同期結果を返却

        Args:
            user: 対象ユーザー
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            project_id: プロジェクトID（指定時はそのプロジェクトのみ）

        Returns:
            同期結果の辞書
            {
                "success": True,
                "created": 5,   # 新規作成したタスク数
                "updated": 10,  # 更新したタスク数
                "total": 15     # 処理したタスク総数
            }

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - 同期履歴はsync_historyテーブルに記録されます
            - タスクの担当者・報告者が存在しない場合は自動的に作成されます

        Example:
            result = await task_sync_service.sync_user_tasks(
                user=current_user,
                access_token="abc123...",
                db=db,
                project_id=None  # 全プロジェクトのタスク
            )
            print(f"新規: {result['created']}件、更新: {result['updated']}件")
        """
        logger.info(f"ユーザータスク同期開始: " f"user_id={user.id}, project_id={project_id}")

        # 同期履歴を作成
        sync_history = self._create_sync_history(
            db=db, user_id=user.id, sync_type=SyncType.USER_TASKS, target_id=project_id, target_name=f"User {user.name} tasks"
        )

        try:
            # Backlogから課題を取得
            issues = await backlog_client.get_user_issues(user.backlog_id, access_token, project_id=project_id)

            logger.info(f"課題を取得しました: {len(issues)}件")

            # 共通処理で同期を実行
            return await self._sync_issues_common(issues, sync_history, db)

        except Exception as e:
            self._handle_sync_error(error=e, sync_history=sync_history, db=db, context="ユーザータスク同期")
            raise

    async def sync_project_tasks(
        self, project: Project, access_token: str, db: Session, user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        プロジェクトのタスクを同期

        指定されたプロジェクトの全てのタスクをBacklogから取得し、
        ローカルデータベースと同期します。

        処理フロー:
            1. 同期履歴を作成（SyncType.PROJECT_TASKS）
            2. Backlogからプロジェクトの課題を取得
            3. 各課題をタスクとして同期
            4. 同期履歴を完了としてマーク
            5. 同期結果を返却

        Args:
            project: 対象プロジェクト
            access_token: Backlog APIアクセストークン
            db: データベースセッション
            user: 同期を実行するユーザー（同期履歴記録用、オプション）

        Returns:
            同期結果の辞書
            {
                "success": True,
                "created": 8,   # 新規作成したタスク数
                "updated": 15,  # 更新したタスク数
                "total": 23     # 処理したタスク総数
            }

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - userが指定されない場合、同期履歴は作成されません
            - タスクの担当者・報告者が存在しない場合は自動的に作成されます
            - プロジェクトIDは自動的にタスクに設定されます

        Example:
            result = await task_sync_service.sync_project_tasks(
                project=project,
                access_token="abc123...",
                db=db,
                user=current_user
            )
            print(f"新規: {result['created']}件、更新: {result['updated']}件")
        """
        logger.info(f"プロジェクトタスク同期開始: " f"project_id={project.id}, user_id={user.id if user else None}")

        # 同期履歴を作成（userが渡されない場合はNone）
        sync_history = None
        if user:
            sync_history = self._create_sync_history(
                db=db,
                user_id=user.id,
                sync_type=SyncType.PROJECT_TASKS,
                target_id=project.id,
                target_name=f"Project: {project.name}",
            )

        try:
            # Backlogから課題を取得
            issues = await backlog_client.get_project_issues(project.backlog_id, access_token)

            logger.info(f"課題を取得しました: {len(issues)}件")

            # 共通処理で同期を実行（project_idを指定）
            return await self._sync_issues_common(issues=issues, sync_history=sync_history, db=db, project_id=project.id)

        except Exception as e:
            self._handle_sync_error(error=e, sync_history=sync_history, db=db, context="プロジェクトタスク同期")
            raise

    async def sync_single_issue(self, issue_id: int, access_token: str, db: Session) -> Task:
        """
        単一の課題を同期

        指定されたIDの課題をBacklogから取得し、同期します。

        Args:
            issue_id: Backlog課題ID
            access_token: Backlog APIアクセストークン
            db: データベースセッション

        Returns:
            同期されたタスクオブジェクト

        Raises:
            Exception: Backlog APIエラー、データベースエラーなど

        Note:
            - この処理では同期履歴は作成されません
            - 即座にコミットされます

        Example:
            task = await task_sync_service.sync_single_issue(
                issue_id=12345,
                access_token="abc123...",
                db=db
            )
        """
        try:
            # Backlogから課題を取得
            issue_data = await backlog_client.get_issue_by_id(issue_id, access_token)

            # タスクを同期
            task = await self._sync_issue(issue_data, db)

            db.commit()

            logger.info(f"単一課題同期完了: " f"issue_id={issue_id}, task_id={task.id}")

            return task

        except Exception as e:
            logger.error(f"単一課題同期失敗: issue_id={issue_id}, error={str(e)}", exc_info=True)
            db.rollback()
            raise

    async def get_sync_status(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        同期状況を取得

        指定されたプロジェクトのタスク同期状況を取得します。

        Args:
            project_id: プロジェクトID
            db: データベースセッション

        Returns:
            同期状況の辞書
            {
                "total_tasks": 50,
                "status_counts": {
                    "TODO": 10,
                    "IN_PROGRESS": 15,
                    "RESOLVED": 20,
                    "CLOSED": 5
                },
                "last_sync": "2025-01-15T10:30:00Z"  # または None
            }

        Example:
            status = await task_sync_service.get_sync_status(
                project_id=1,
                db=db
            )
            print(f"タスク総数: {status['total_tasks']}")
        """
        # タスク総数を取得
        total_tasks = db.query(Task).filter(Task.project_id == project_id).count()

        # ステータス別の件数を取得
        status_counts = {}
        for status in TaskStatus:
            count = db.query(Task).filter(Task.project_id == project_id, Task.status == status).count()
            status_counts[status.value] = count

        # 最終同期日時を取得
        last_sync = db.query(Task.updated_at).filter(Task.project_id == project_id).order_by(Task.updated_at.desc()).first()

        logger.debug(f"同期状況を取得: project_id={project_id}, " f"total_tasks={total_tasks}")

        return {"total_tasks": total_tasks, "status_counts": status_counts, "last_sync": last_sync[0] if last_sync else None}

    async def _sync_issues_common(
        self, issues: List[dict], sync_history: Optional[SyncHistory], db: Session, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        課題同期の共通処理

        複数の課題を一括で同期し、結果を返します。
        ユーザータスク同期とプロジェクトタスク同期の両方で使用されます。

        Args:
            issues: 同期する課題のリスト
            sync_history: 同期履歴オブジェクト（Optional）
            db: データベースセッション
            project_id: プロジェクトID（課題作成時に指定）

        Returns:
            同期結果の辞書
            {
                "success": True,
                "created": 5,
                "updated": 10,
                "total": 15
            }

        Note:
            - 各課題の同期に失敗してもエラーは発生しません（ログに記録されます）
            - 同期履歴がある場合、自動的に完了としてマークされます
            - 処理完了後、コミットされます

        Raises:
            Exception: データベースエラーなど
        """
        created_count = 0
        updated_count = 0

        try:
            for issue_data in issues:
                try:
                    # 課題を同期
                    task = await self._sync_issue(issue_data=issue_data, db=db, project_id=project_id)

                    # 新規作成か更新かを判定
                    if task.created_at == task.updated_at:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    logger.error(
                        f"課題の同期に失敗: "
                        f"issue_id={issue_data.get('id')}, "
                        f"issue_key={issue_data.get('issueKey')}, "
                        f"error={str(e)}",
                        exc_info=True,
                    )
                    # 個別の課題同期失敗は全体の処理を止めない
                    continue

            # 同期履歴を完了としてマーク
            if sync_history:
                sync_history.complete(items_created=created_count, items_updated=updated_count, total_items=len(issues))

            db.commit()

            logger.info(f"課題同期完了: " f"created={created_count}, updated={updated_count}, " f"total={len(issues)}")

            return {"success": True, "created": created_count, "updated": updated_count, "total": len(issues)}

        except Exception as e:
            logger.error(f"課題同期の共通処理でエラー: {str(e)}", exc_info=True)
            if sync_history:
                sync_history.fail(str(e))
            db.rollback()
            raise

    async def _sync_issue(self, issue_data: dict, db: Session, project_id: Optional[int] = None) -> Task:
        """
        課題データを同期（内部メソッド）

        Backlogから取得した課題データを元に、既存のタスクを更新するか、
        新規作成します。

        処理内容:
            - 基本情報（タイトル、説明、ステータスなど）
            - 担当者・報告者（存在しない場合は自動作成）
            - プロジェクト情報
            - 優先度、課題種別
            - 工数（見積もり・実績）
            - 日付（開始日、期日、完了日）
            - マイルストーン、カテゴリー、バージョン

        Args:
            issue_data: Backlog APIから取得した課題データ
            db: データベースセッション
            project_id: プロジェクトID（指定時は優先的に使用）

        Returns:
            同期されたタスクオブジェクト

        Note:
            - backlog_idで既存タスクを検索します
            - 存在しない場合は新規作成します
            - db.flush()は呼び出しません（呼び出し側でコミットが必要）
            - ステータスマッピングに存在しないステータスはTODOとして扱われます

        Example:
            task = await self._sync_issue(
                issue_data=issue_data,
                db=db,
                project_id=1
            )
        """
        # 既存のタスクを検索
        task = db.query(Task).filter(Task.backlog_id == issue_data["id"]).first()

        if not task:
            task = Task(backlog_id=issue_data["id"])
            db.add(task)
            logger.debug(f"新規タスクを作成: " f"backlog_id={issue_data['id']}, " f"issue_key={issue_data['issueKey']}")
        else:
            logger.debug(
                f"既存タスクを更新: " f"id={task.id}, backlog_id={issue_data['id']}, " f"issue_key={issue_data['issueKey']}"
            )

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
            # 引数で指定されたプロジェクトIDを優先
            task.project_id = project_id
        elif issue_data.get("projectId"):
            # BacklogプロジェクトIDから内部プロジェクトIDを取得
            project = db.query(Project).filter(Project.backlog_id == issue_data["projectId"]).first()
            if project:
                task.project_id = project.id

        # 担当者（存在しない場合は自動作成）
        if issue_data.get("assignee"):
            assignee = self._get_or_create_user(issue_data["assignee"], db)
            task.assignee_id = assignee.id

        # 報告者（存在しない場合は自動作成）
        if issue_data.get("createdUser"):
            reporter = self._get_or_create_user(issue_data["createdUser"], db)
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


# シングルトンインスタンス
task_sync_service = TaskSyncService()
