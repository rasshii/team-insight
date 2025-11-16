"""
個人ダッシュボードサービス - ビジネスロジック層

このモジュールは、個人ダッシュボードに関するビジネスロジックを提供します。
API層から複雑なクエリとビジネスロジックを分離し、保守性とテスタビリティを向上させます。

主要機能:
1. 個人ダッシュボードデータの取得と集計
2. KPIサマリーの計算（完了率、平均処理時間等）
3. 作業フロー分析（各ステータスでの滞留時間）
4. 生産性トレンド分析（日別完了タスク数）
5. スキルマトリックス計算（タスクタイプ別処理効率）
6. 最近のアクティビティ取得

レイヤー構成:
- API層（analytics.py）: HTTPリクエスト/レスポンス処理
- Service層（このファイル）: ビジネスロジック、複数リポジトリの調整
- Repository層: データアクセス

パフォーマンス最適化:
- 複数の統計を単一クエリで集計（CASE式の活用）
- eager loading（joinedload）でN+1問題を回避
- Backlog API呼び出しの最小化

使用例:
    dashboard_service = DashboardService(db, user_id=1)
    dashboard_data = await dashboard_service.get_personal_dashboard_data(period_days=30)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_

from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.project import Project, project_members
from app.models.auth import OAuthToken
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.backlog_client import backlog_client

logger = logging.getLogger(__name__)


class DashboardService:
    """
    個人ダッシュボードのビジネスロジックを提供するサービス

    ユーザーの生産性とパフォーマンスを可視化するための包括的なデータを生成します。
    複雑なSQLクエリ、Backlog API連携、データ集計を担当し、API層をシンプルに保ちます。

    主要メソッド:
    - get_personal_dashboard_data: ダッシュボード全体のデータを取得
    - get_kpi_summary: KPI指標のサマリーを計算
    - get_workflow_analysis: 作業フロー分析（ステータス別滞留時間）
    - get_productivity_trend: 生産性トレンド（日別完了数）
    - get_skill_matrix: スキルマトリックス（タスクタイプ別効率）
    - get_recent_completed_tasks: 最近完了したタスク

    依存関係:
    - TaskRepository: タスクデータへのアクセス
    - UserRepository: ユーザーデータへのアクセス
    - BacklogClient: Backlog APIからのステータス名取得

    Attributes:
        db (Session): データベースセッション
        user_id (int): 対象ユーザーのID
        task_repo (TaskRepository): タスクリポジトリ
        user_repo (UserRepository): ユーザーリポジトリ
    """

    def __init__(self, db: Session, user_id: int):
        """
        DashboardServiceの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            user_id (int): ダッシュボード表示対象のユーザーID
        """
        self.db = db
        self.user_id = user_id
        self.task_repo = TaskRepository(db)
        self.user_repo = UserRepository(db)

    async def get_personal_dashboard_data(self, period_days: int = 30, user: Optional[User] = None) -> Dict[str, Any]:
        """
        個人ダッシュボードの包括的なデータを取得

        ユーザーの生産性とパフォーマンスを可視化するための全データを
        1回のメソッド呼び出しで取得します。内部的には複数のメソッドを
        呼び出して各種統計を集計し、統合されたデータを返します。

        処理フロー:
            1. KPIサマリーを取得（タスク数、完了率、平均処理時間）
            2. 作業フロー分析を実行（各ステータスでの滞留時間）
            3. 生産性トレンドを分析（指定期間の日別完了タスク数）
            4. スキルマトリックスを計算（タスクタイプ別の処理効率）
            5. 最近完了したタスクを取得（直近5件）
            6. 全データを統合して返却

        Args:
            period_days (int, optional):
                生産性トレンド分析の対象期間（日数）。デフォルトは30日。
                7日、30日、90日などが一般的。
            user (Optional[User], optional):
                ユーザーオブジェクト。Backlog連携時のステータス名取得に使用。
                Noneの場合はデフォルトのステータス名を使用。

        Returns:
            Dict[str, Any]: ダッシュボードの包括的なデータ
            {
                "user_id": int,
                "user_name": str,
                "kpi_summary": {
                    "total_tasks": int,
                    "completed_tasks": int,
                    "in_progress_tasks": int,
                    "overdue_tasks": int,
                    "completion_rate": float,
                    "average_completion_days": float
                },
                "workflow_analysis": [
                    {
                        "status": str,
                        "status_name": str,
                        "average_days": float
                    },
                    ...
                ],
                "productivity_trend": [
                    {
                        "date": str (ISO format),
                        "completed_count": int
                    },
                    ...
                ],
                "skill_matrix": [
                    {
                        "task_type": str,
                        "total_count": int,
                        "average_completion_days": float
                    },
                    ...
                ],
                "recent_completed_tasks": [
                    {
                        "id": int,
                        "title": str,
                        "project_name": str,
                        "completed_date": str (ISO format)
                    },
                    ...
                ]
            }

        Raises:
            Exception: データベースエラーまたはBacklog API呼び出しエラー

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> data = await service.get_personal_dashboard_data(period_days=30)
            >>> print(f"Completion rate: {data['kpi_summary']['completion_rate']}%")
            >>> print(f"Tasks completed in last 30 days: {len(data['productivity_trend'])}")

        Note:
            - ユーザーが存在しない場合でも空のデータ構造を返します
            - Backlog API呼び出しが失敗しても、デフォルトのステータス名で処理を継続
            - パフォーマンス最適化のため、各統計クエリは並列実行可能
        """
        # ユーザー情報を取得（userが渡されていない場合）
        if user is None:
            user = self.user_repo.get(self.user_id)
            if not user:
                logger.warning(f"User not found: {self.user_id}")
                # ユーザーが見つからない場合でも空のデータを返す
                return self._empty_dashboard_data()

        # 各種統計データを取得（並列実行可能）
        kpi_summary = self.get_kpi_summary()
        workflow_analysis = await self.get_workflow_analysis(user)
        productivity_trend = self.get_productivity_trend(period_days)
        skill_matrix = self.get_skill_matrix()
        recent_tasks = self.get_recent_completed_tasks(limit=5)

        return {
            "user_id": user.id,
            "user_name": user.name,
            "kpi_summary": kpi_summary,
            "workflow_analysis": workflow_analysis,
            "productivity_trend": productivity_trend,
            "skill_matrix": skill_matrix,
            "recent_completed_tasks": recent_tasks,
        }

    def get_kpi_summary(self) -> Dict[str, Any]:
        """
        KPIサマリーを取得

        タスクの基本統計を単一のクエリで効率的に集計します。
        総タスク数、各ステータスのタスク数、完了率、平均処理時間を計算。

        集計される指標:
        - total_tasks: ユーザーに割り当てられた総タスク数
        - completed_tasks: 完了したタスク数
        - in_progress_tasks: 進行中のタスク数
        - overdue_tasks: 期限切れで未完了のタスク数
        - completion_rate: 完了率（%）
        - average_completion_days: 完了タスクの平均処理日数

        パフォーマンス最適化:
        - CASE式を使用して1回のクエリで複数の集計を実行
        - COUNT、SUM、AVGを組み合わせた効率的な集計
        - インデックスを活用した高速クエリ

        Returns:
            Dict[str, Any]: KPIサマリー
            {
                "total_tasks": int,
                "completed_tasks": int,
                "in_progress_tasks": int,
                "overdue_tasks": int,
                "completion_rate": float (0-100),
                "average_completion_days": float
            }

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> kpi = service.get_kpi_summary()
            >>> print(f"Completion rate: {kpi['completion_rate']:.1f}%")
            >>> print(f"Average completion time: {kpi['average_completion_days']:.1f} days")

        Note:
            - 完了率は小数点第1位まで四捨五入
            - 平均処理時間は作成日時から完了日時までの日数
            - タスクが0件の場合、completion_rateは0を返す
        """
        # 基本統計を一度に取得（パフォーマンス最適化）
        stats = (
            self.db.query(
                func.count(Task.id).label("total"),
                func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label("completed"),
                func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label("in_progress"),
                func.sum(case((and_(Task.due_date < datetime.now(), Task.status != TaskStatus.CLOSED), 1), else_=0)).label(
                    "overdue"
                ),
            )
            .filter(Task.assignee_id == self.user_id)
            .first()
        )

        total_tasks = stats.total or 0
        completed_tasks = stats.completed or 0
        in_progress_tasks = stats.in_progress or 0
        overdue_tasks = stats.overdue or 0

        # 平均処理時間を計算（完了タスクのみ）
        # 作成日時から完了日時までの秒数を日数に変換
        avg_completion_time = (
            self.db.query(func.avg(func.extract("epoch", Task.completed_date - Task.created_at) / 86400))
            .filter(Task.assignee_id == self.user_id, Task.status == TaskStatus.CLOSED, Task.completed_date.isnot(None))
            .scalar()
        )

        # 完了率を計算（0除算を回避）
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round(completion_rate, 1),
            "average_completion_days": round(avg_completion_time, 1) if avg_completion_time else 0,
        }

    async def get_workflow_analysis(self, user: Optional[User] = None) -> List[Dict[str, Any]]:
        """
        作業フロー分析を実行

        各タスクステータスでの平均滞留時間を分析します。
        Backlog APIと連携してカスタムステータス名も取得し、
        より分かりやすい表示名を提供します。

        分析内容:
        - 各ステータス（TODO、IN_PROGRESS、RESOLVED、CLOSED）での平均滞留日数
        - 完了タスク: 作成から完了までの時間
        - 未完了タスク: 最終更新からの経過時間

        ステータス名の決定:
        1. Backlog APIからカスタムステータス名を取得（OAuth連携時）
        2. 取得できない場合はデフォルトのステータス名を使用
        3. ステータスIDとステータス名の両方でマッピング

        処理フロー:
            1. ユーザーの所属プロジェクトを取得
            2. OAuth トークンの存在を確認
            3. 各プロジェクトのカスタムステータスをBacklog APIから取得
            4. ステータス名のマッピングテーブルを作成
            5. 各ステータスでの平均滞留時間をクエリ
            6. ステータス名を適用して結果を返却

        Args:
            user (Optional[User], optional):
                ユーザーオブジェクト。Backlog連携時に使用。
                Noneの場合はuser_idから取得するか、デフォルト名を使用。

        Returns:
            List[Dict[str, Any]]: ステータス別の作業フロー分析結果
            [
                {
                    "status": str (例: "TODO"),
                    "status_name": str (例: "未対応" または カスタム名),
                    "average_days": float
                },
                ...
            ]

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> workflow = await service.get_workflow_analysis(user)
            >>> for item in workflow:
            ...     print(f"{item['status_name']}: {item['average_days']} days")
            未対応: 2.1 days
            処理中: 1.8 days
            処理済み: 0.5 days
            完了: 3.2 days

        Note:
            - Backlog API呼び出しが失敗してもデフォルト名で処理を継続
            - 複数プロジェクトのステータスを統合してマッピング
            - カスタムステータスがある場合は優先的に使用

        Raises:
            Exception: データベースエラーが発生した場合
        """
        # ユーザーの所属プロジェクトを取得
        user_projects = self.db.query(Project).join(project_members).filter(project_members.c.user_id == self.user_id).all()

        # ステータスIDと名前のマッピングを作成
        status_name_map = {}

        # OAuth トークンを取得してBacklog APIからカスタムステータス名を取得
        oauth_token = (
            self.db.query(OAuthToken).filter(OAuthToken.user_id == self.user_id, OAuthToken.provider == "backlog").first()
        )

        # Backlog APIからカスタムステータス名を取得
        if oauth_token and user_projects:
            for project in user_projects:
                try:
                    statuses = await backlog_client.get_issue_statuses(
                        project_id=project.backlog_id, access_token=oauth_token.access_token
                    )
                    for status in statuses:
                        # ステータス名をキーにしてマッピング（大文字小文字を無視）
                        status_name_map[status["name"].upper()] = status["name"]
                        # IDベースのマッピングも作成
                        status_name_map[str(status["id"])] = status["name"]
                except Exception as e:
                    # Backlog API呼び出しが失敗しても処理を継続
                    logger.warning(f"Failed to get statuses for project {project.id}: {str(e)}")

        # デフォルトのステータス名マッピング
        default_status_names = {"TODO": "未対応", "IN_PROGRESS": "処理中", "RESOLVED": "処理済み", "CLOSED": "完了"}

        # 各ステータスでの滞留時間を分析
        workflow_analysis = []
        for task_status in TaskStatus:
            if task_status == TaskStatus.CLOSED:
                # 完了タスク: 作成から完了までの時間
                avg_time = (
                    self.db.query(func.avg(func.extract("epoch", Task.completed_date - Task.created_at) / 86400))
                    .filter(Task.assignee_id == self.user_id, Task.status == task_status, Task.completed_date.isnot(None))
                    .scalar()
                )
            else:
                # 未完了タスク: 更新日からの経過時間
                avg_time = (
                    self.db.query(func.avg(func.extract("epoch", datetime.now() - Task.updated_at) / 86400))
                    .filter(Task.assignee_id == self.user_id, Task.status == task_status)
                    .scalar()
                )

            # ステータス名を取得（カスタムステータス名があればそれを使用）
            status_value = task_status.value
            status_display_name = status_name_map.get(
                status_value.upper(), default_status_names.get(status_value, status_value)
            )

            workflow_analysis.append(
                {
                    "status": status_value,
                    "status_name": status_display_name,
                    "average_days": round(avg_time, 1) if avg_time else 0,
                }
            )

        return workflow_analysis

    def get_productivity_trend(self, period_days: int = 30) -> List[Dict[str, Any]]:
        """
        生産性トレンドを取得

        指定期間内の日別完了タスク数を集計し、生産性の推移を可視化します。
        グラフ表示用のデータとして最適な形式で返却します。

        集計内容:
        - 指定期間内に完了したタスクを日付別にグループ化
        - 各日付の完了タスク数をカウント
        - 日付順にソート

        Args:
            period_days (int, optional):
                分析対象期間（日数）。デフォルトは30日。
                現在日時から指定日数前までのデータを集計。

        Returns:
            List[Dict[str, Any]]: 日別の完了タスク数
            [
                {
                    "date": str (ISO format, 例: "2025-01-15"),
                    "completed_count": int
                },
                ...
            ]

            日付の昇順でソートされています。

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> trend = service.get_productivity_trend(period_days=7)
            >>> for day in trend:
            ...     print(f"{day['date']}: {day['completed_count']} tasks")
            2025-01-10: 3 tasks
            2025-01-11: 5 tasks
            2025-01-12: 2 tasks

        Note:
            - タスクを完了していない日は結果に含まれません
            - 完了日時（completed_date）が期間内のタスクのみ集計
            - DATE関数によるグループ化で日付部分のみを使用

        パフォーマンス最適化:
        - GROUP BYによる効率的な集計
        - インデックスを活用した高速フィルタリング
        - 必要最小限のカラムのみ取得
        """
        # 集計開始日を計算
        start_date = datetime.now() - timedelta(days=period_days)

        # 日別の完了タスク数を集計
        productivity_trend = (
            self.db.query(func.date(Task.completed_date).label("date"), func.count(Task.id).label("completed_count"))
            .filter(Task.assignee_id == self.user_id, Task.status == TaskStatus.CLOSED, Task.completed_date >= start_date)
            .group_by(func.date(Task.completed_date))
            .all()
        )

        # ISO形式の日付文字列に変換
        trend_data = [
            {"date": date.isoformat() if date else None, "completed_count": count} for date, count in productivity_trend
        ]

        return trend_data

    def get_skill_matrix(self) -> List[Dict[str, Any]]:
        """
        スキルマトリックスを取得

        タスクタイプ（課題種別）別の処理効率を分析します。
        どのタイプのタスクが得意か、どのタイプに時間がかかっているかを把握できます。

        分析内容:
        - タスクタイプ別の総タスク数
        - タスクタイプ別の平均完了日数
        - 完了タスクのみを対象とした処理時間分析

        Returns:
            List[Dict[str, Any]]: タスクタイプ別の処理効率
            [
                {
                    "task_type": str (例: "バグ", "タスク", "要望"),
                    "total_count": int,
                    "average_completion_days": float または None
                },
                ...
            ]

            task_typeがNoneのタスクは除外されます。

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> matrix = service.get_skill_matrix()
            >>> for item in matrix:
            ...     print(f"{item['task_type']}: {item['total_count']} tasks, "
            ...           f"avg {item['average_completion_days']} days")
            バグ: 20 tasks, avg 2.5 days
            タスク: 45 tasks, avg 3.8 days
            要望: 12 tasks, avg 5.2 days

        Note:
            - 完了していないタスクは平均日数の計算に含まれません
            - タスクタイプが設定されていないタスクは除外
            - 作成から完了までの日数を計算

        パフォーマンス最適化:
        - GROUP BYによる効率的な集計
        - CASE式で完了タスクのみの平均を計算
        - COUNT、AVGを組み合わせた1回のクエリ
        """
        # タスクタイプ別の処理効率を集計
        skill_matrix = (
            self.db.query(
                Task.issue_type_name,
                func.count(Task.id).label("count"),
                func.avg(
                    case(
                        (
                            Task.status == TaskStatus.CLOSED,
                            func.extract("epoch", Task.completed_date - Task.created_at) / 86400,
                        ),
                        else_=None,
                    )
                ).label("avg_completion_days"),
            )
            .filter(Task.assignee_id == self.user_id)
            .group_by(Task.issue_type_name)
            .all()
        )

        # タスクタイプがNoneでないものだけを返す
        skill_data = []
        for issue_type_name, count, avg_days in skill_matrix:
            if issue_type_name:
                skill_data.append(
                    {
                        "task_type": issue_type_name,
                        "total_count": count,
                        "average_completion_days": round(avg_days, 1) if avg_days else None,
                    }
                )

        return skill_data

    def get_recent_completed_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        最近完了したタスクを取得

        直近に完了したタスクのリストを取得し、ダッシュボードに表示します。
        プロジェクト情報も含めて効率的に取得（N+1問題対策）。

        Args:
            limit (int, optional):
                取得するタスク数。デフォルトは5件。

        Returns:
            List[Dict[str, Any]]: 最近完了したタスクのリスト
            [
                {
                    "id": int,
                    "title": str,
                    "project_name": str または None,
                    "completed_date": str (ISO format) または None
                },
                ...
            ]

            完了日時の降順（新しい順）でソートされています。

        Example:
            >>> service = DashboardService(db, user_id=1)
            >>> recent = service.get_recent_completed_tasks(limit=10)
            >>> for task in recent:
            ...     print(f"{task['completed_date']}: {task['title']}")
            2025-01-15T14:30:00: ログイン機能のバグ修正
            2025-01-15T10:15:00: データベース最適化

        Note:
            - CLOSEDステータスのタスクのみ取得
            - joinedloadでプロジェクト情報を事前ロード（N+1問題回避）
            - プロジェクトが削除されている場合はproject_nameがNone

        パフォーマンス最適化:
        - joinedload()による関連データの効率的な取得
        - 必要最小限のカラムのみ返却
        - LIMITによる取得件数の制限
        """
        # 最近完了したタスクを取得（関連データをeager loading）
        recent_completed = (
            self.db.query(Task)
            .options(joinedload(Task.project), joinedload(Task.assignee))
            .filter(Task.assignee_id == self.user_id, Task.status == TaskStatus.CLOSED)
            .order_by(Task.completed_date.desc())
            .limit(limit)
            .all()
        )

        # レスポンス用のデータに変換
        return [
            {
                "id": task.id,
                "title": task.title,
                "project_name": task.project.name if task.project else None,
                "completed_date": task.completed_date.isoformat() if task.completed_date else None,
            }
            for task in recent_completed
        ]

    def _empty_dashboard_data(self) -> Dict[str, Any]:
        """
        空のダッシュボードデータを返す

        ユーザーが存在しない場合やエラー時に使用する
        デフォルトの空データ構造を提供します。

        Returns:
            Dict[str, Any]: 空のダッシュボードデータ
        """
        return {
            "user_id": self.user_id,
            "user_name": "Unknown",
            "kpi_summary": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "overdue_tasks": 0,
                "completion_rate": 0,
                "average_completion_days": 0,
            },
            "workflow_analysis": [],
            "productivity_trend": [],
            "skill_matrix": [],
            "recent_completed_tasks": [],
        }
