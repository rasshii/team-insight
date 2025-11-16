"""
タスクリポジトリ - タスクデータアクセス層

このモジュールは、タスクモデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. タスクの基本的なCRUD操作
2. Backlogキーによる検索
3. ユーザー、プロジェクト、ステータスによるフィルタリング
4. タスク統計情報の取得
5. 期限切れタスクの検出
6. パフォーマンス分析用のクエリ

パフォーマンス最適化：
- joinedload()による関連データの効率的な取得
- インデックスを活用した高速検索
- N+1問題の回避
- 集計クエリの最適化

使用例：
    task_repo = TaskRepository(db)

    # Backlogキーで検索
    task = task_repo.get_by_backlog_key("PROJECT-123")

    # ユーザーのタスク一覧
    tasks = task_repo.get_user_tasks(user_id=1, filters={"status": "TODO"})

    # タスク統計
    stats = task_repo.get_statistics(project_id=1)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case, desc

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project
from app.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    タスクリポジトリクラス

    タスクモデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、タスク特有の検索・集計機能を実装。

    主要メソッド：
    - get_by_backlog_key: Backlogキーで検索
    - get_by_backlog_id: Backlog IDで検索
    - get_user_tasks: ユーザーのタスク一覧
    - get_project_tasks: プロジェクトのタスク一覧
    - get_overdue_tasks: 期限切れタスクの取得
    - get_statistics: タスク統計情報の取得
    - get_recent_completed: 最近完了したタスク

    リレーション最適化：
    - joinedload()による効率的な関連データ取得
    - サブクエリを活用した集計
    - N+1問題の完全回避
    """

    def __init__(self, db: Session):
        """
        TaskRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(Task, db)

    def get_by_backlog_key(self, backlog_key: str) -> Optional[Task]:
        """
        Backlogキーでタスクを検索

        Backlogキー（例: "PROJECT-123"）は一意制約があり、
        タスクを識別する主要な方法です。

        Args:
            backlog_key (str): Backlogキー（例: "PROJECT-123"）

        Returns:
            Optional[Task]: 見つかった場合はTaskインスタンス、見つからない場合はNone

        Example:
            >>> task = task_repo.get_by_backlog_key("PROJECT-123")
            >>> if task:
            ...     print(f"Task: {task.title}")

        Note:
            - Backlogキーは一意制約
            - インデックスによる高速検索
        """
        return self.db.query(Task).filter(Task.backlog_key == backlog_key).first()

    def get_by_backlog_id(self, backlog_id: int) -> Optional[Task]:
        """
        Backlog IDでタスクを検索

        BacklogシステムのタスクIDで検索します。
        backlog_idは一意制約があり、高速な検索が可能です。

        Args:
            backlog_id (int): BacklogタスクID

        Returns:
            Optional[Task]: 見つかった場合はTaskインスタンス、見つからない場合はNone

        Example:
            >>> task = task_repo.get_by_backlog_id(12345)
            >>> if task:
            ...     print(f"Backlog task: {task.title}")

        Note:
            - Backlog連携タスクのみ保持
            - インデックスによる高速検索
        """
        return self.db.query(Task).filter(Task.backlog_id == backlog_id).first()

    def get_with_relations(self, task_id: int) -> Optional[Task]:
        """
        関連情報を含めてタスクを取得（N+1問題対策）

        タスク情報と関連するプロジェクト、担当者、報告者の情報を
        1回のクエリで効率的に取得します。

        取得されるデータ：
        - タスク基本情報
        - プロジェクト情報
        - 担当者（User）情報
        - 報告者（User）情報

        Args:
            task_id (int): タスクID

        Returns:
            Optional[Task]:
                見つかった場合は関連情報を含むTaskインスタンス、
                見つからない場合はNone

        Example:
            >>> task = task_repo.get_with_relations(1)
            >>> if task:
            ...     print(f"Task: {task.title}")
            ...     print(f"Project: {task.project.name}")
            ...     print(f"Assignee: {task.assignee.name}")

        Note:
            - task.project, task.assignee, task.reporterが事前ロード済み
            - 追加のクエリは発行されない（N+1問題なし）
        """
        return (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
            .filter(Task.id == task_id)
            .first()
        )

    def get_user_tasks(
        self, user_id: int, filters: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """
        ユーザーのタスク一覧を取得（フィルタリング対応）

        指定されたユーザーに割り当てられたタスクを取得します。
        ステータス、期限、プロジェクトなどでフィルタリング可能。

        フィルタ可能な条件：
        - status: タスクステータス（TaskStatus）
        - project_id: プロジェクトID
        - is_overdue: 期限切れフラグ（True/False）
        - priority: 優先度

        Args:
            user_id (int): ユーザーID
            filters (Optional[Dict[str, Any]], optional):
                フィルタ条件の辞書。デフォルトはNone
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Task]: ユーザーのタスクリスト

        Example:
            >>> # 未完了のタスクを取得
            >>> tasks = task_repo.get_user_tasks(
            ...     user_id=1,
            ...     filters={"status": TaskStatus.TODO}
            ... )

            >>> # 期限切れタスクを取得
            >>> overdue_tasks = task_repo.get_user_tasks(
            ...     user_id=1,
            ...     filters={"is_overdue": True}
            ... )

        Note:
            - 担当者（assignee_id）でフィルタリング
            - プロジェクト情報も効率的に取得（joinedload）
        """
        query = (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
            .filter(Task.assignee_id == user_id)
        )

        # フィルタ条件の適用
        if filters:
            if "status" in filters:
                query = query.filter(Task.status == filters["status"])

            if "project_id" in filters:
                query = query.filter(Task.project_id == filters["project_id"])

            if "is_overdue" in filters and filters["is_overdue"]:
                # 期限切れかつ未完了のタスク
                query = query.filter(and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED))

            if "priority" in filters:
                query = query.filter(Task.priority == filters["priority"])

        # 更新日時の降順でソート
        query = query.order_by(desc(Task.updated_at))

        return query.offset(skip).limit(limit).all()

    def get_project_tasks(
        self, project_id: int, filters: Optional[Dict[str, Any]] = None, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """
        プロジェクトのタスク一覧を取得（フィルタリング対応）

        指定されたプロジェクトのタスクを取得します。
        ステータス、担当者、期限などでフィルタリング可能。

        フィルタ可能な条件：
        - status: タスクステータス（TaskStatus）
        - assignee_id: 担当者のユーザーID
        - is_overdue: 期限切れフラグ（True/False）
        - priority: 優先度

        Args:
            project_id (int): プロジェクトID
            filters (Optional[Dict[str, Any]], optional):
                フィルタ条件の辞書。デフォルトはNone
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Task]: プロジェクトのタスクリスト

        Example:
            >>> # プロジェクトの未完了タスクを取得
            >>> tasks = task_repo.get_project_tasks(
            ...     project_id=1,
            ...     filters={"status": TaskStatus.TODO}
            ... )

        Note:
            - 担当者、報告者情報も効率的に取得（joinedload）
        """
        query = (
            self.db.query(Task)
            .options(joinedload(Task.assignee), joinedload(Task.reporter))
            .filter(Task.project_id == project_id)
        )

        # フィルタ条件の適用
        if filters:
            if "status" in filters:
                query = query.filter(Task.status == filters["status"])

            if "assignee_id" in filters:
                query = query.filter(Task.assignee_id == filters["assignee_id"])

            if "is_overdue" in filters and filters["is_overdue"]:
                # 期限切れかつ未完了のタスク
                query = query.filter(and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED))

            if "priority" in filters:
                query = query.filter(Task.priority == filters["priority"])

        # 更新日時の降順でソート
        query = query.order_by(desc(Task.updated_at))

        return query.offset(skip).limit(limit).all()

    def get_overdue_tasks(
        self, user_id: Optional[int] = None, project_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """
        期限切れタスクを取得

        期限が過ぎているが未完了のタスクを取得します。
        ユーザーまたはプロジェクトで絞り込み可能。

        Args:
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            project_id (Optional[int], optional):
                プロジェクトIDで絞り込み。Noneの場合は全プロジェクト
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Task]: 期限切れタスクのリスト

        Example:
            >>> # ユーザーの期限切れタスク
            >>> overdue = task_repo.get_overdue_tasks(user_id=1)
            >>> print(f"Overdue tasks: {len(overdue)}")

            >>> # プロジェクトの期限切れタスク
            >>> overdue = task_repo.get_overdue_tasks(project_id=1)

        Note:
            - 期限切れかつ未完了（CLOSED以外）のタスクのみ
            - 期限の近いものから順にソート
        """
        query = (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee))
            .filter(and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED))
        )

        # ユーザーでフィルタリング
        if user_id is not None:
            query = query.filter(Task.assignee_id == user_id)

        # プロジェクトでフィルタリング
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)

        # 期限の近いものから順にソート
        query = query.order_by(Task.due_date.asc())

        return query.offset(skip).limit(limit).all()

    def get_statistics(
        self,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        タスク統計情報を取得

        プロジェクトまたはユーザーのタスク統計を集計します。
        期間を指定することで、特定期間の統計を取得可能。

        集計される統計情報：
        - total_tasks: 総タスク数
        - completed_tasks: 完了タスク数
        - in_progress_tasks: 進行中タスク数
        - todo_tasks: 未着手タスク数
        - overdue_tasks: 期限切れタスク数
        - completion_rate: 完了率（%）
        - avg_completion_days: 平均完了日数

        Args:
            project_id (Optional[int], optional):
                プロジェクトIDで絞り込み。Noneの場合は全プロジェクト
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            start_date (Optional[datetime], optional):
                集計開始日時。Noneの場合は制限なし
            end_date (Optional[datetime], optional):
                集計終了日時。Noneの場合は制限なし

        Returns:
            Dict[str, Any]: タスク統計情報の辞書

        Example:
            >>> # プロジェクトの統計
            >>> stats = task_repo.get_statistics(project_id=1)
            >>> print(f"Completion rate: {stats['completion_rate']:.1f}%")

            >>> # ユーザーの今月の統計
            >>> from datetime import datetime
            >>> start = datetime.now().replace(day=1, hour=0, minute=0)
            >>> stats = task_repo.get_statistics(
            ...     user_id=1,
            ...     start_date=start
            ... )

        Note:
            - 1回のクエリで複数の統計を効率的に取得
            - CASE式による条件付き集計を活用
        """
        # ベースクエリ
        query = self.db.query(Task)

        # フィルタ条件の適用
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)

        if user_id is not None:
            query = query.filter(Task.assignee_id == user_id)

        if start_date is not None:
            query = query.filter(Task.created_at >= start_date)

        if end_date is not None:
            query = query.filter(Task.created_at <= end_date)

        # 統計情報を一括取得
        stats = query.with_entities(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label("completed"),
            func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label("in_progress"),
            func.sum(case((Task.status == TaskStatus.TODO, 1), else_=0)).label("todo"),
            func.sum(case((and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED), 1), else_=0)).label(
                "overdue"
            ),
            func.avg(func.extract("epoch", Task.completed_date - Task.created_at) / 86400).label("avg_completion_days"),
        ).first()

        total_tasks = stats.total or 0
        completed_tasks = stats.completed or 0
        in_progress_tasks = stats.in_progress or 0
        todo_tasks = stats.todo or 0
        overdue_tasks = stats.overdue or 0
        avg_completion_days = stats.avg_completion_days or 0

        # 完了率を計算
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "todo_tasks": todo_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round(completion_rate, 1),
            "avg_completion_days": round(avg_completion_days, 1),
        }

    def get_recent_completed(
        self, project_id: Optional[int] = None, user_id: Optional[int] = None, days: int = 7, limit: int = 100
    ) -> List[Task]:
        """
        最近完了したタスクを取得

        指定された期間内に完了したタスクを新しい順に取得します。

        Args:
            project_id (Optional[int], optional):
                プロジェクトIDで絞り込み。Noneの場合は全プロジェクト
            user_id (Optional[int], optional):
                ユーザーIDで絞り込み。Noneの場合は全ユーザー
            days (int, optional): 過去何日間のタスクを取得するか。デフォルトは7日
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[Task]: 最近完了したタスクのリスト

        Example:
            >>> # 過去7日間に完了したタスク
            >>> recent = task_repo.get_recent_completed(project_id=1, days=7)
            >>> for task in recent:
            ...     print(f"Completed: {task.title}")

        Note:
            - 完了日時の新しいものから順にソート
            - プロジェクト、担当者情報も効率的に取得
        """
        start_date = datetime.now() - timedelta(days=days)

        query = (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee))
            .filter(and_(Task.status == TaskStatus.CLOSED, Task.completed_date >= start_date))
        )

        # フィルタ条件の適用
        if project_id is not None:
            query = query.filter(Task.project_id == project_id)

        if user_id is not None:
            query = query.filter(Task.assignee_id == user_id)

        # 完了日時の降順でソート
        query = query.order_by(desc(Task.completed_date))

        return query.limit(limit).all()

    def count_user_tasks(self, user_id: int, status: Optional[TaskStatus] = None) -> int:
        """
        ユーザーのタスク数をカウント

        Args:
            user_id (int): ユーザーID
            status (Optional[TaskStatus], optional):
                ステータスで絞り込み。Noneの場合は全ステータス

        Returns:
            int: タスク数

        Example:
            >>> # 全タスク数
            >>> total = task_repo.count_user_tasks(user_id=1)

            >>> # 未完了タスク数
            >>> todo = task_repo.count_user_tasks(
            ...     user_id=1, status=TaskStatus.TODO
            ... )

        Note:
            - COUNT(*)による高速カウント
        """
        query = self.db.query(func.count(Task.id)).filter(Task.assignee_id == user_id)

        if status is not None:
            query = query.filter(Task.status == status)

        return query.scalar() or 0

    def count_project_tasks(self, project_id: int, status: Optional[TaskStatus] = None) -> int:
        """
        プロジェクトのタスク数をカウント

        Args:
            project_id (int): プロジェクトID
            status (Optional[TaskStatus], optional):
                ステータスで絞り込み。Noneの場合は全ステータス

        Returns:
            int: タスク数

        Example:
            >>> # 全タスク数
            >>> total = task_repo.count_project_tasks(project_id=1)

            >>> # 完了タスク数
            >>> completed = task_repo.count_project_tasks(
            ...     project_id=1, status=TaskStatus.CLOSED
            ... )

        Note:
            - COUNT(*)による高速カウント
        """
        query = self.db.query(func.count(Task.id)).filter(Task.project_id == project_id)

        if status is not None:
            query = query.filter(Task.status == status)

        return query.scalar() or 0
