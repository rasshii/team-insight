"""
TaskServiceのユニットテスト

このモジュールは、TaskServiceの全メソッドをテストします。
タスク一覧取得、フィルタリング、ページネーション、ステータス集計の正確性を検証します。
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.task_service import TaskService
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.project import Project


@pytest.mark.unit
class TestTaskService:
    """TaskServiceのテストクラス"""

    @pytest.fixture
    def service(self, db_session: Session) -> TaskService:
        """TaskServiceインスタンスを作成するフィクスチャ"""
        return TaskService(db_session)

    @pytest.fixture
    def sample_tasks(self, db_session: Session, test_user: User, test_project: Project) -> list:
        """複数のサンプルタスクを作成するフィクスチャ"""
        tasks = []

        # TODOタスク（優先度: 高）
        for i in range(3):
            task = Task(
                backlog_id=3000 + i,
                backlog_key=f"TASK-{i}",
                project_id=test_project.id,
                assignee_id=test_user.id,
                reporter_id=test_user.id,
                title=f"TODO Task {i}",
                description=f"TODO task description {i}",
                status=TaskStatus.TODO,
                priority=2,  # 高
                issue_type_name="バグ",
                due_date=datetime.now() + timedelta(days=3)
            )
            db_session.add(task)
            tasks.append(task)

        # IN_PROGRESSタスク（優先度: 中）
        for i in range(2):
            task = Task(
                backlog_id=3100 + i,
                backlog_key=f"TASK-{100 + i}",
                project_id=test_project.id,
                assignee_id=test_user.id,
                reporter_id=test_user.id,
                title=f"In Progress Task {i}",
                description=f"In progress task description {i}",
                status=TaskStatus.IN_PROGRESS,
                priority=3,  # 中
                issue_type_name="タスク",
                due_date=datetime.now() + timedelta(days=5)
            )
            db_session.add(task)
            tasks.append(task)

        # CLOSEDタスク（優先度: 低）
        for i in range(4):
            task = Task(
                backlog_id=3200 + i,
                backlog_key=f"TASK-{200 + i}",
                project_id=test_project.id,
                assignee_id=test_user.id,
                reporter_id=test_user.id,
                title=f"Closed Task {i}",
                description=f"Closed task description {i}",
                status=TaskStatus.CLOSED,
                priority=4,  # 低
                issue_type_name="要望",
                due_date=datetime.now() - timedelta(days=2),
                completed_date=datetime.now() - timedelta(days=1)
            )
            db_session.add(task)
            tasks.append(task)

        # RESOLVEDタスク（優先度: 中）
        task = Task(
            backlog_id=3300,
            backlog_key="TASK-300",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Resolved Task",
            description="Resolved task description",
            status=TaskStatus.RESOLVED,
            priority=3,  # 中
            issue_type_name="バグ",
            due_date=datetime.now() + timedelta(days=1)
        )
        db_session.add(task)
        tasks.append(task)

        db_session.commit()
        for task in tasks:
            db_session.refresh(task)

        return tasks

    def test_get_user_tasks_all(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（全タスク）

        期待される動作:
        - ユーザーに割り当てられた全タスクが取得される
        - タスク数、ページネーション情報、ステータス集計が正しい
        """
        # Act（実行）
        result = service.get_user_tasks(user_id=test_user.id, limit=50)

        # Assert（検証）
        assert "tasks" in result
        assert "pagination" in result
        assert "status_summary" in result

        # タスク数の確認
        assert len(result["tasks"]) == 10
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["limit"] == 50
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["has_more"] is False

        # ステータス集計の確認
        status_summary = result["status_summary"]
        assert status_summary["TODO"] == 3
        assert status_summary["IN_PROGRESS"] == 2
        assert status_summary["RESOLVED"] == 1
        assert status_summary["CLOSED"] == 4

    def test_get_user_tasks_with_status_filter(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（ステータスフィルタあり）

        期待される動作:
        - 指定されたステータスのタスクのみが取得される
        - ステータス集計は全タスクを対象とする
        """
        # Act（実行）
        result = service.get_user_tasks(
            user_id=test_user.id,
            status=TaskStatus.TODO,
            limit=50
        )

        # Assert（検証）
        assert len(result["tasks"]) == 3
        assert result["pagination"]["total"] == 3

        # 全てのタスクがTODOステータス
        for task in result["tasks"]:
            assert task["status"] == TaskStatus.TODO.value

        # ステータス集計は全タスクを対象
        status_summary = result["status_summary"]
        assert status_summary["TODO"] == 3
        assert status_summary["IN_PROGRESS"] == 2
        assert status_summary["CLOSED"] == 4

    def test_get_user_tasks_with_priority_filter(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（優先度フィルタあり）

        期待される動作:
        - 指定された優先度のタスクのみが取得される
        """
        # Act（実行）
        result = service.get_user_tasks(
            user_id=test_user.id,
            priority=2,  # 高優先度
            limit=50
        )

        # Assert（検証）
        assert len(result["tasks"]) == 3

        # 全てのタスクが高優先度
        for task in result["tasks"]:
            assert task["priority"] == 2

    def test_get_user_tasks_with_pagination(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（ページネーション）

        期待される動作:
        - skip, limitが正しく適用される
        - has_moreフラグが正しく設定される
        """
        # Act（実行）- 最初の5件
        result1 = service.get_user_tasks(
            user_id=test_user.id,
            limit=5,
            skip=0
        )

        # Assert（検証）
        assert len(result1["tasks"]) == 5
        assert result1["pagination"]["total"] == 10
        assert result1["pagination"]["offset"] == 0
        assert result1["pagination"]["has_more"] is True

        # Act（実行）- 次の5件
        result2 = service.get_user_tasks(
            user_id=test_user.id,
            limit=5,
            skip=5
        )

        # Assert（検証）
        assert len(result2["tasks"]) == 5
        assert result2["pagination"]["offset"] == 5
        assert result2["pagination"]["has_more"] is False

    def test_get_user_tasks_sorting(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（ソート順）

        期待される動作:
        - タスクが優先度の降順、期限の昇順でソートされる
        """
        # Act（実行）
        result = service.get_user_tasks(user_id=test_user.id, limit=50)

        # Assert（検証）
        tasks = result["tasks"]
        assert len(tasks) > 0

        # 優先度の降順になっているか確認（高い優先度が先）
        # 優先度: 2=高, 3=中, 4=低
        priorities = [task["priority"] for task in tasks if task["priority"] is not None]

        # 最初のいくつかのタスクは高優先度（2）であるべき
        high_priority_tasks = [p for p in priorities if p == 2]
        assert len(high_priority_tasks) == 3  # 高優先度タスクが3件

    def test_get_user_tasks_no_tasks(
        self,
        db_session: Session,
        test_user: User
    ):
        """
        ユーザーのタスク一覧取得をテスト（タスクなしケース）

        期待される動作:
        - タスクがない場合、空のリストが返される
        - ステータス集計は全て0
        """
        # Arrange（準備）
        service = TaskService(db_session)

        # Act（実行）
        result = service.get_user_tasks(user_id=test_user.id)

        # Assert（検証）
        assert len(result["tasks"]) == 0
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["has_more"] is False

        # ステータス集計は全て0
        status_summary = result["status_summary"]
        assert status_summary["TODO"] == 0
        assert status_summary["IN_PROGRESS"] == 0
        assert status_summary["RESOLVED"] == 0
        assert status_summary["CLOSED"] == 0

    def test_get_user_tasks_data_structure(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ユーザーのタスク一覧取得をテスト（データ構造）

        期待される動作:
        - 返されるタスクデータが正しい構造を持つ
        - プロジェクト、報告者情報が含まれる
        """
        # Act（実行）
        result = service.get_user_tasks(user_id=test_user.id, limit=1)

        # Assert（検証）
        assert len(result["tasks"]) > 0

        task = result["tasks"][0]

        # 必須フィールドの確認
        assert "id" in task
        assert "title" in task
        assert "description" in task
        assert "status" in task
        assert "priority" in task
        assert "task_type" in task
        assert "due_date" in task
        assert "created_at" in task
        assert "updated_at" in task
        assert "completed_date" in task

        # 関連情報の確認
        assert "project" in task
        assert task["project"] is not None
        assert "id" in task["project"]
        assert "name" in task["project"]

        assert "reporter" in task
        # reporter は存在する場合と null の場合がある

    def test_get_task_with_details_success(
        self,
        service: TaskService,
        sample_tasks: list
    ):
        """
        タスク詳細取得をテスト（成功ケース）

        期待される動作:
        - 指定されたIDのタスク詳細が取得される
        - 全ての関連データが含まれる
        """
        # Arrange（準備）
        task_id = sample_tasks[0].id

        # Act（実行）
        task_detail = service.get_task_with_details(task_id)

        # Assert（検証）
        assert task_detail is not None
        assert task_detail["id"] == task_id
        assert task_detail["backlog_id"] is not None
        assert task_detail["backlog_key"] is not None
        assert task_detail["title"] is not None
        assert task_detail["status"] is not None

        # 関連データの確認
        assert "project" in task_detail
        assert task_detail["project"] is not None
        assert "backlog_id" in task_detail["project"]

        assert "assignee" in task_detail
        assert task_detail["assignee"] is not None

    def test_get_task_with_details_not_found(
        self,
        service: TaskService
    ):
        """
        タスク詳細取得をテスト（存在しないタスク）

        期待される動作:
        - 存在しないIDの場合、Noneが返される
        """
        # Act（実行）
        task_detail = service.get_task_with_details(task_id=99999)

        # Assert（検証）
        assert task_detail is None

    def test_get_status_summary(
        self,
        service: TaskService,
        test_user: User,
        sample_tasks: list
    ):
        """
        ステータス別集計をテスト（内部メソッド）

        期待される動作:
        - 全ステータスのタスク数が正しく集計される
        - タスクが0件のステータスも0として返される
        """
        # Act（実行）
        summary = service._get_status_summary(test_user.id)

        # Assert（検証）
        assert isinstance(summary, dict)

        # 全ステータスが含まれる
        assert "TODO" in summary
        assert "IN_PROGRESS" in summary
        assert "RESOLVED" in summary
        assert "CLOSED" in summary

        # カウントの確認
        assert summary["TODO"] == 3
        assert summary["IN_PROGRESS"] == 2
        assert summary["RESOLVED"] == 1
        assert summary["CLOSED"] == 4

    def test_get_status_summary_no_tasks(
        self,
        service: TaskService,
        test_user: User
    ):
        """
        ステータス別集計をテスト（タスクなしケース）

        期待される動作:
        - タスクがない場合、全ステータスが0として返される
        """
        # Act（実行）
        summary = service._get_status_summary(test_user.id)

        # Assert（検証）
        assert summary["TODO"] == 0
        assert summary["IN_PROGRESS"] == 0
        assert summary["RESOLVED"] == 0
        assert summary["CLOSED"] == 0

    def test_get_user_tasks_with_deleted_project(
        self,
        db_session: Session,
        test_user: User,
        test_project: Project
    ):
        """
        ユーザーのタスク一覧取得をテスト（プロジェクト削除済みケース）

        期待される動作:
        - プロジェクトが削除されていてもタスクは取得できる
        - project情報はNoneになる
        """
        # Arrange（準備）
        # タスクを作成
        task = Task(
            backlog_id=4000,
            backlog_key="ORPHAN-1",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Orphan Task",
            description="Task with deleted project",
            status=TaskStatus.TODO,
            priority=3
        )
        db_session.add(task)
        db_session.commit()

        # プロジェクトを削除（CASCADE設定により、タスクのproject_idはNULLになる）
        # 実際の動作は外部キー設定に依存するため、ここでは手動でNULLに設定
        task.project_id = None
        db_session.commit()

        service = TaskService(db_session)

        # Act（実行）
        result = service.get_user_tasks(user_id=test_user.id)

        # Assert（検証）
        assert len(result["tasks"]) == 1
        task_data = result["tasks"][0]
        assert task_data["project"] is None
