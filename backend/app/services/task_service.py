"""
タスクサービス - ビジネスロジック層

このモジュールは、タスク管理に関するビジネスロジックを提供します。
API層から複雑なクエリとビジネスロジックを分離し、保守性とテスタビリティを向上させます。

主要機能:
1. タスク一覧の取得（フィルタリング、ページネーション）
2. タスクのステータス別集計
3. タスクの優先度によるソート
4. タスクの詳細情報取得（関連データ含む）

レイヤー構成:
- API層（analytics.py）: HTTPリクエスト/レスポンス処理
- Service層（このファイル）: ビジネスロジック、バリデーション
- Repository層: データアクセス

パフォーマンス最適化:
- eager loading（joinedload）でN+1問題を回避
- ステータス別集計を単一クエリで実行
- インデックスを活用した高速フィルタリング

使用例:
    task_service = TaskService(db)
    result = task_service.get_user_tasks(
        user_id=1,
        status="TODO",
        limit=50
    )
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.task import Task, TaskStatus
from app.repositories.task_repository import TaskRepository

logger = logging.getLogger(__name__)


class TaskService:
    """
    タスク管理のビジネスロジックを提供するサービス

    ユーザーのタスク一覧取得、フィルタリング、ソート、
    ステータス別集計などのビジネスロジックを担当します。

    主要メソッド:
    - get_user_tasks: ユーザーのタスク一覧を取得
    - get_task_with_details: タスク詳細を関連データ込みで取得
    - get_status_summary: ステータス別タスク数の集計

    依存関係:
    - TaskRepository: タスクデータへのアクセス

    Attributes:
        db (Session): データベースセッション
        task_repo (TaskRepository): タスクリポジトリ
    """

    def __init__(self, db: Session):
        """
        TaskServiceの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        self.db = db
        self.task_repo = TaskRepository(db)

    def get_user_tasks(
        self, user_id: int, status: Optional[TaskStatus] = None, priority: Optional[int] = None, skip: int = 0, limit: int = 50
    ) -> Dict[str, Any]:
        """
        ユーザーのタスク一覧を取得

        指定されたユーザーに割り当てられているタスクの一覧を取得します。
        ステータスや優先度によるフィルタリング、ページネーションに対応。

        処理フロー:
            1. クエリベースを構築（ユーザーIDでフィルタ）
            2. 関連データ（プロジェクト、担当者、報告者）をeager loading
            3. ステータスフィルタを適用（指定された場合）
            4. 総件数を取得（ページネーション用）
            5. タスク一覧を取得（優先度と期限でソート）
            6. ステータス別集計を取得
            7. 結果を統合して返却

        フィルタリング:
        - status: タスクステータスで絞り込み（TODO、IN_PROGRESS等）
        - priority: 優先度で絞り込み（2=高、3=中、4=低）

        ソート:
        - 優先度の降順（高い優先度が先）
        - 期限の昇順（期限が近いものが先）

        Args:
            user_id (int): ユーザーID
            status (Optional[TaskStatus], optional):
                フィルタリングするタスクステータス。
                Noneの場合は全ステータスを取得。
            priority (Optional[int], optional):
                フィルタリングする優先度。
                Noneの場合は全優先度を取得。
            skip (int, optional):
                スキップするレコード数（オフセット）。
                デフォルトは0。ページネーションに使用。
            limit (int, optional):
                取得する最大レコード数。
                デフォルトは50。ページネーションに使用。

        Returns:
            Dict[str, Any]: タスク一覧と関連情報
            {
                "tasks": [
                    {
                        "id": int,
                        "title": str,
                        "description": str,
                        "status": str,
                        "priority": int,
                        "task_type": str,
                        "due_date": str (ISO format) または None,
                        "created_at": str (ISO format),
                        "updated_at": str (ISO format),
                        "completed_date": str (ISO format) または None,
                        "project": {
                            "id": int,
                            "name": str
                        } または None,
                        "reporter": {
                            "id": int,
                            "name": str
                        } または None
                    },
                    ...
                ],
                "pagination": {
                    "total": int,
                    "limit": int,
                    "offset": int,
                    "has_more": bool
                },
                "status_summary": {
                    "TODO": int,
                    "IN_PROGRESS": int,
                    "RESOLVED": int,
                    "CLOSED": int
                }
            }

        Example:
            >>> service = TaskService(db)
            >>> result = service.get_user_tasks(
            ...     user_id=1,
            ...     status=TaskStatus.TODO,
            ...     limit=20
            ... )
            >>> print(f"Total TODO tasks: {result['status_summary']['TODO']}")
            >>> for task in result['tasks']:
            ...     print(f"{task['title']} - {task['status']}")

        Note:
            - プロジェクト、報告者情報はeager loadingで効率的に取得
            - N+1問題を完全に回避
            - 削除されたプロジェクト/ユーザーの場合はNoneを返す

        パフォーマンス最適化:
        - joinedload()による関連データの事前ロード
        - ステータス別集計は別クエリで効率的に実行
        - インデックスを活用した高速ソート
        """
        # クエリ構築（関連データをeager loading）
        query = (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
            .filter(Task.assignee_id == user_id)
        )

        # ステータスフィルタ
        if status:
            query = query.filter(Task.status == status)

        # 優先度フィルタ
        if priority is not None:
            query = query.filter(Task.priority == priority)

        # 総件数を取得（ページネーション用）
        total_count = query.count()

        # タスク一覧を取得（優先度と期限でソート）
        tasks = query.order_by(Task.priority.desc(), Task.due_date.asc()).limit(limit).offset(skip).all()

        # ステータス別集計を取得
        status_summary = self._get_status_summary(user_id)

        # タスクリストをレスポンス形式に変換
        task_list = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority,
                "task_type": task.issue_type_name,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "completed_date": task.completed_date.isoformat() if task.completed_date else None,
                "project": {"id": task.project.id, "name": task.project.name} if task.project else None,
                "reporter": {"id": task.reporter.id, "name": task.reporter.name} if task.reporter else None,
            }
            for task in tasks
        ]

        return {
            "tasks": task_list,
            "pagination": {"total": total_count, "limit": limit, "offset": skip, "has_more": skip + limit < total_count},
            "status_summary": status_summary,
        }

    def get_task_with_details(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        タスク詳細を関連データ込みで取得

        指定されたIDのタスクを、プロジェクト、担当者、報告者などの
        関連データと共に効率的に取得します。

        Args:
            task_id (int): タスクID

        Returns:
            Optional[Dict[str, Any]]: タスク詳細情報またはNone
            タスクが見つからない場合はNoneを返します。

            {
                "id": int,
                "backlog_id": int,
                "backlog_key": str,
                "title": str,
                "description": str,
                "status": str,
                "priority": int,
                "task_type": str,
                "estimated_hours": float または None,
                "actual_hours": float または None,
                "due_date": str (ISO format) または None,
                "created_at": str (ISO format),
                "updated_at": str (ISO format),
                "completed_date": str (ISO format) または None,
                "project": {
                    "id": int,
                    "name": str,
                    "backlog_id": int
                } または None,
                "assignee": {
                    "id": int,
                    "name": str,
                    "email": str
                } または None,
                "reporter": {
                    "id": int,
                    "name": str,
                    "email": str
                } または None
            }

        Example:
            >>> service = TaskService(db)
            >>> task = service.get_task_with_details(task_id=123)
            >>> if task:
            ...     print(f"Task: {task['title']}")
            ...     print(f"Project: {task['project']['name']}")

        Note:
            - N+1問題を回避するためにjoinedloadを使用
            - 関連データが削除されている場合はNoneを返す
        """
        task = self.task_repo.get_with_relations(task_id)

        if not task:
            return None

        return {
            "id": task.id,
            "backlog_id": task.backlog_id,
            "backlog_key": task.backlog_key,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority,
            "task_type": task.issue_type_name,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "completed_date": task.completed_date.isoformat() if task.completed_date else None,
            "project": (
                {"id": task.project.id, "name": task.project.name, "backlog_id": task.project.backlog_id}
                if task.project
                else None
            ),
            "assignee": (
                {"id": task.assignee.id, "name": task.assignee.name, "email": task.assignee.email} if task.assignee else None
            ),
            "reporter": (
                {"id": task.reporter.id, "name": task.reporter.name, "email": task.reporter.email} if task.reporter else None
            ),
        }

    def _get_status_summary(self, user_id: int) -> Dict[str, int]:
        """
        ステータス別タスク数の集計（内部メソッド）

        指定されたユーザーのタスクをステータス別に集計します。
        効率的な単一クエリで全ステータスのカウントを取得。

        Args:
            user_id (int): ユーザーID

        Returns:
            Dict[str, int]: ステータス別タスク数
            {
                "TODO": int,
                "IN_PROGRESS": int,
                "RESOLVED": int,
                "CLOSED": int
            }

            全てのステータスが含まれ、タスクが0件の場合も0を返します。

        Example:
            >>> summary = service._get_status_summary(user_id=1)
            >>> print(f"TODO: {summary['TODO']}")
            TODO: 15

        Note:
            - GROUP BYによる効率的な集計
            - 全ステータスを含む辞書を返す（0件の場合も0を設定）
        """
        # ステータス別集計
        status_counts_query = (
            self.db.query(Task.status, func.count(Task.id)).filter(Task.assignee_id == user_id).group_by(Task.status).all()
        )

        # 全ステータスを含む辞書を初期化（0件でも表示）
        status_counts = {status.value: 0 for status in TaskStatus}

        # 集計結果を辞書に設定
        for task_status, count in status_counts_query:
            status_counts[task_status.value] = count

        return status_counts
