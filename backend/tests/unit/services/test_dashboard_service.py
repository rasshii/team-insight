"""
DashboardServiceのユニットテスト

このモジュールは、DashboardServiceの全メソッドをテストします。
KPI計算、作業フロー分析、生産性トレンド、スキルマトリックスの正確性を検証します。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken


@pytest.mark.unit
class TestDashboardService:
    """DashboardServiceのテストクラス"""

    @pytest.fixture
    def service(self, db_session: Session, test_user: User) -> DashboardService:
        """DashboardServiceインスタンスを作成するフィクスチャ"""
        return DashboardService(db_session, test_user.id)

    @pytest.fixture
    def sample_tasks(self, db_session: Session, test_user: User, test_project: Project) -> list:
        """複数のサンプルタスクを作成するフィクスチャ"""
        tasks = []

        # 完了タスク（3日前に作成、1日前に完了）
        for i in range(3):
            task = Task(
                backlog_id=2000 + i,
                backlog_key=f"DASH-{i}",
                project_id=test_project.id,
                assignee_id=test_user.id,
                reporter_id=test_user.id,
                title=f"Completed Task {i}",
                description=f"Completed task description {i}",
                status=TaskStatus.CLOSED,
                priority=TaskPriority.MEDIUM,
                issue_type_name="バグ",
                due_date=datetime.now() - timedelta(days=2),
                completed_date=datetime.now() - timedelta(days=1),
                created_at=datetime.now() - timedelta(days=3)
            )
            db_session.add(task)
            tasks.append(task)

        # 進行中タスク
        for i in range(2):
            task = Task(
                backlog_id=2100 + i,
                backlog_key=f"DASH-{100 + i}",
                project_id=test_project.id,
                assignee_id=test_user.id,
                reporter_id=test_user.id,
                title=f"In Progress Task {i}",
                description=f"In progress task description {i}",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                issue_type_name="タスク",
                due_date=datetime.now() + timedelta(days=5)
            )
            db_session.add(task)
            tasks.append(task)

        # TODOタスク
        task = Task(
            backlog_id=2200,
            backlog_key="DASH-200",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="TODO Task",
            description="TODO task description",
            status=TaskStatus.TODO,
            priority=TaskPriority.LOW,
            issue_type_name="要望",
            due_date=datetime.now() + timedelta(days=10)
        )
        db_session.add(task)
        tasks.append(task)

        # 期限切れタスク
        task = Task(
            backlog_id=2300,
            backlog_key="DASH-300",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Overdue Task",
            description="Overdue task description",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            issue_type_name="バグ",
            due_date=datetime.now() - timedelta(days=5)
        )
        db_session.add(task)
        tasks.append(task)

        db_session.commit()
        for task in tasks:
            db_session.refresh(task)

        return tasks

    def test_get_kpi_summary_with_tasks(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        KPIサマリーの取得をテスト（タスクありケース）

        期待される動作:
        - 総タスク数、完了数、進行中数、期限切れ数が正しく集計される
        - 完了率が正しく計算される
        - 平均完了日数が正しく計算される
        """
        # Act（実行）
        kpi = service.get_kpi_summary()

        # Assert（検証）
        assert kpi["total_tasks"] == 7
        assert kpi["completed_tasks"] == 3
        assert kpi["in_progress_tasks"] == 2
        assert kpi["overdue_tasks"] == 1  # 期限切れかつ未完了
        assert kpi["completion_rate"] == pytest.approx(42.9, rel=0.1)  # 3/7 * 100
        assert kpi["average_completion_days"] > 0  # 完了タスクがあるので0より大きい

    def test_get_kpi_summary_no_tasks(
        self,
        db_session: Session,
        test_user: User
    ):
        """
        KPIサマリーの取得をテスト（タスクなしケース）

        期待される動作:
        - タスクが0件でも正常に動作する
        - 全ての値が0になる
        """
        # Arrange（準備）
        service = DashboardService(db_session, test_user.id)

        # Act（実行）
        kpi = service.get_kpi_summary()

        # Assert（検証）
        assert kpi["total_tasks"] == 0
        assert kpi["completed_tasks"] == 0
        assert kpi["in_progress_tasks"] == 0
        assert kpi["overdue_tasks"] == 0
        assert kpi["completion_rate"] == 0
        assert kpi["average_completion_days"] == 0

    @pytest.mark.asyncio
    async def test_get_workflow_analysis_without_backlog(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        作業フロー分析の取得をテスト（Backlog連携なしケース）

        期待される動作:
        - 各ステータスの平均滞留時間が計算される
        - デフォルトのステータス名が使用される
        - 全ステータスが含まれる
        """
        # Act（実行）
        workflow = await service.get_workflow_analysis()

        # Assert（検証）
        assert len(workflow) == 4  # TODO, IN_PROGRESS, RESOLVED, CLOSED

        # ステータス名の検証
        status_names = {item["status"]: item["status_name"] for item in workflow}
        assert status_names["TODO"] == "未対応"
        assert status_names["IN_PROGRESS"] == "処理中"
        assert status_names["RESOLVED"] == "処理済み"
        assert status_names["CLOSED"] == "完了"

        # 平均日数が設定されていることを確認
        for item in workflow:
            assert "average_days" in item
            assert item["average_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_workflow_analysis_with_backlog(
        self,
        db_session: Session,
        test_user: User,
        test_project: Project,
        sample_tasks: list
    ):
        """
        作業フロー分析の取得をテスト（Backlog連携ありケース）

        期待される動作:
        - Backlog APIからカスタムステータス名を取得
        - カスタムステータス名が使用される
        """
        # Arrange（準備）
        # OAuth トークンを作成
        oauth_token = OAuthToken(
            user_id=test_user.id,
            provider="backlog",
            access_token="test_access_token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        db_session.add(oauth_token)
        db_session.commit()

        # プロジェクトとユーザーを紐付け
        test_project.members.append(test_user)
        db_session.commit()

        service = DashboardService(db_session, test_user.id)

        # Backlog APIのモック
        mock_statuses = [
            {"id": 1, "name": "未着手"},
            {"id": 2, "name": "対応中"},
            {"id": 3, "name": "レビュー待ち"},
            {"id": 4, "name": "完了"}
        ]

        with patch('app.services.dashboard_service.backlog_client.get_issue_statuses',
                   new_callable=AsyncMock, return_value=mock_statuses):
            # Act（実行）
            workflow = await service.get_workflow_analysis(test_user)

            # Assert（検証）
            assert len(workflow) == 4

    def test_get_productivity_trend(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        生産性トレンドの取得をテスト

        期待される動作:
        - 期間内の日別完了タスク数が取得される
        - 日付がISO形式で返される
        """
        # Act（実行）
        trend = service.get_productivity_trend(period_days=30)

        # Assert（検証）
        assert isinstance(trend, list)

        # 完了タスクがあるので、少なくとも1日分のデータがある
        assert len(trend) >= 1

        # データ構造の確認
        if len(trend) > 0:
            assert "date" in trend[0]
            assert "completed_count" in trend[0]
            assert trend[0]["completed_count"] > 0

    def test_get_productivity_trend_no_completed_tasks(
        self,
        db_session: Session,
        test_user: User
    ):
        """
        生産性トレンドの取得をテスト（完了タスクなしケース）

        期待される動作:
        - 完了タスクがない場合、空のリストが返される
        """
        # Arrange（準備）
        service = DashboardService(db_session, test_user.id)

        # Act（実行）
        trend = service.get_productivity_trend(period_days=30)

        # Assert（検証）
        assert isinstance(trend, list)
        assert len(trend) == 0

    def test_get_skill_matrix(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        スキルマトリックスの取得をテスト

        期待される動作:
        - タスクタイプ別の処理効率が計算される
        - タスクタイプ名がNoneでないものだけが返される
        """
        # Act（実行）
        skill_matrix = service.get_skill_matrix()

        # Assert（検証）
        assert isinstance(skill_matrix, list)
        assert len(skill_matrix) > 0

        # タスクタイプが含まれていることを確認
        task_types = {item["task_type"] for item in skill_matrix}
        assert "バグ" in task_types
        assert "タスク" in task_types
        assert "要望" in task_types

        # データ構造の確認
        for item in skill_matrix:
            assert "task_type" in item
            assert item["task_type"] is not None
            assert "total_count" in item
            assert item["total_count"] > 0
            assert "average_completion_days" in item

    def test_get_skill_matrix_no_tasks(
        self,
        db_session: Session,
        test_user: User
    ):
        """
        スキルマトリックスの取得をテスト（タスクなしケース）

        期待される動作:
        - タスクがない場合、空のリストが返される
        """
        # Arrange（準備）
        service = DashboardService(db_session, test_user.id)

        # Act（実行）
        skill_matrix = service.get_skill_matrix()

        # Assert（検証）
        assert isinstance(skill_matrix, list)
        assert len(skill_matrix) == 0

    def test_get_recent_completed_tasks(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        最近完了したタスクの取得をテスト

        期待される動作:
        - 完了タスクが新しい順に返される
        - プロジェクト情報が含まれる
        - 完了日時がISO形式で返される
        """
        # Act（実行）
        recent_tasks = service.get_recent_completed_tasks(limit=5)

        # Assert（検証）
        assert isinstance(recent_tasks, list)
        assert len(recent_tasks) == 3  # 完了タスクは3件

        # データ構造の確認
        for task_data in recent_tasks:
            assert "id" in task_data
            assert "title" in task_data
            assert "project_name" in task_data
            assert task_data["project_name"] is not None
            assert "completed_date" in task_data
            assert task_data["completed_date"] is not None

    def test_get_recent_completed_tasks_with_limit(
        self,
        service: DashboardService,
        sample_tasks: list
    ):
        """
        最近完了したタスクの取得をテスト（件数制限あり）

        期待される動作:
        - 指定された件数以下が返される
        """
        # Act（実行）
        recent_tasks = service.get_recent_completed_tasks(limit=2)

        # Assert（検証）
        assert isinstance(recent_tasks, list)
        assert len(recent_tasks) == 2  # limitで2件に制限

    @pytest.mark.asyncio
    async def test_get_personal_dashboard_data_success(
        self,
        service: DashboardService,
        test_user: User,
        sample_tasks: list
    ):
        """
        個人ダッシュボードデータの取得をテスト（成功ケース）

        期待される動作:
        - 全ての統計データが取得される
        - データ構造が正しい
        """
        # Act（実行）
        dashboard_data = await service.get_personal_dashboard_data(
            period_days=30,
            user=test_user
        )

        # Assert（検証）
        assert "user_id" in dashboard_data
        assert dashboard_data["user_id"] == test_user.id
        assert "user_name" in dashboard_data
        assert dashboard_data["user_name"] == test_user.name

        # KPIサマリーの確認
        assert "kpi_summary" in dashboard_data
        kpi = dashboard_data["kpi_summary"]
        assert kpi["total_tasks"] > 0
        assert kpi["completed_tasks"] >= 0
        assert kpi["completion_rate"] >= 0

        # 作業フロー分析の確認
        assert "workflow_analysis" in dashboard_data
        assert isinstance(dashboard_data["workflow_analysis"], list)
        assert len(dashboard_data["workflow_analysis"]) == 4

        # 生産性トレンドの確認
        assert "productivity_trend" in dashboard_data
        assert isinstance(dashboard_data["productivity_trend"], list)

        # スキルマトリックスの確認
        assert "skill_matrix" in dashboard_data
        assert isinstance(dashboard_data["skill_matrix"], list)

        # 最近完了したタスクの確認
        assert "recent_completed_tasks" in dashboard_data
        assert isinstance(dashboard_data["recent_completed_tasks"], list)

    @pytest.mark.asyncio
    async def test_get_personal_dashboard_data_user_not_found(
        self,
        db_session: Session
    ):
        """
        個人ダッシュボードデータの取得をテスト（ユーザー不在ケース）

        期待される動作:
        - ユーザーが存在しない場合、空のダッシュボードデータが返される
        """
        # Arrange（準備）
        # 存在しないユーザーID
        service = DashboardService(db_session, user_id=99999)

        # Act（実行）
        dashboard_data = await service.get_personal_dashboard_data()

        # Assert（検証）
        assert dashboard_data["user_id"] == 99999
        assert dashboard_data["user_name"] == "Unknown"
        assert dashboard_data["kpi_summary"]["total_tasks"] == 0
        assert len(dashboard_data["workflow_analysis"]) == 0
        assert len(dashboard_data["productivity_trend"]) == 0
        assert len(dashboard_data["skill_matrix"]) == 0
        assert len(dashboard_data["recent_completed_tasks"]) == 0
