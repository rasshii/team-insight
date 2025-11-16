"""
TaskRepositoryのユニットテスト

このモジュールは、TaskRepositoryの全メソッドをテストします。
タスク検索、フィルタリング、統計情報取得の正確性を検証します。
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.project import Project


@pytest.mark.unit
class TestTaskRepository:
    """TaskRepositoryのテストクラス"""

    @pytest.fixture
    def sample_task(self, db_session: Session, test_user: User, test_project: Project) -> Task:
        """サンプルタスクを作成するフィクスチャ"""
        task = Task(
            backlog_id=1001,
            backlog_key="TEST-1",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Sample Task",
            description="This is a sample task",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            due_date=datetime.now() + timedelta(days=7)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    @pytest.fixture
    def overdue_task(self, db_session: Session, test_user: User, test_project: Project) -> Task:
        """期限切れタスクを作成するフィクスチャ"""
        task = Task(
            backlog_id=1002,
            backlog_key="TEST-2",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Overdue Task",
            description="This task is overdue",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=datetime.now() - timedelta(days=3)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    @pytest.fixture
    def completed_task(self, db_session: Session, test_user: User, test_project: Project) -> Task:
        """完了済みタスクを作成するフィクスチャ"""
        task = Task(
            backlog_id=1003,
            backlog_key="TEST-3",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Completed Task",
            description="This task is completed",
            status=TaskStatus.CLOSED,
            priority=TaskPriority.MEDIUM,
            due_date=datetime.now() - timedelta(days=1),
            completed_date=datetime.now() - timedelta(hours=5)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    def test_get_by_backlog_key_success(self, db_session: Session, sample_task: Task):
        """
        Backlogキーによるタスク検索をテスト（成功ケース）

        期待される動作:
        - 存在するBacklogキーで正しいタスクが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        found_task = repo.get_by_backlog_key(sample_task.backlog_key)

        # Assert（検証）
        assert found_task is not None
        assert found_task.id == sample_task.id
        assert found_task.backlog_key == sample_task.backlog_key
        assert found_task.title == sample_task.title

    def test_get_by_backlog_key_not_found(self, db_session: Session):
        """
        Backlogキーによるタスク検索をテスト（存在しないケース）

        期待される動作:
        - 存在しないBacklogキーでNoneが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        not_found_task = repo.get_by_backlog_key("NOTEXIST-999")

        # Assert（検証）
        assert not_found_task is None

    def test_get_by_backlog_id_success(self, db_session: Session, sample_task: Task):
        """
        Backlog IDによるタスク検索をテスト（成功ケース）

        期待される動作:
        - 存在するBacklog IDで正しいタスクが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        found_task = repo.get_by_backlog_id(sample_task.backlog_id)

        # Assert（検証）
        assert found_task is not None
        assert found_task.id == sample_task.id
        assert found_task.backlog_id == sample_task.backlog_id

    def test_get_with_relations(self, db_session: Session, sample_task: Task):
        """
        関連情報を含むタスク取得をテスト（N+1問題対策の確認）

        期待される動作:
        - タスク情報とプロジェクト、担当者、報告者情報が1回のクエリで取得される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        found_task = repo.get_with_relations(sample_task.id)

        # Assert（検証）
        assert found_task is not None
        assert found_task.id == sample_task.id
        # 関連情報が事前ロードされているか確認
        assert found_task.project is not None
        assert found_task.assignee is not None
        assert found_task.reporter is not None

    def test_get_user_tasks_without_filters(
        self,
        db_session: Session,
        test_user: User,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        ユーザータスク一覧取得をテスト（フィルタなし）

        期待される動作:
        - ユーザーに割り当てられた全タスクが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        tasks = repo.get_user_tasks(user_id=test_user.id)

        # Assert（検証）
        assert len(tasks) == 3
        task_ids = [t.id for t in tasks]
        assert sample_task.id in task_ids
        assert overdue_task.id in task_ids
        assert completed_task.id in task_ids

    def test_get_user_tasks_with_status_filter(
        self,
        db_session: Session,
        test_user: User,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        ユーザータスク一覧取得をテスト（ステータスフィルタあり）

        期待される動作:
        - 指定されたステータスのタスクのみが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        todo_tasks = repo.get_user_tasks(
            user_id=test_user.id,
            filters={"status": TaskStatus.TODO}
        )

        # Assert（検証）
        assert len(todo_tasks) == 1
        assert todo_tasks[0].id == sample_task.id
        assert todo_tasks[0].status == TaskStatus.TODO

    def test_get_user_tasks_with_overdue_filter(
        self,
        db_session: Session,
        test_user: User,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        ユーザータスク一覧取得をテスト（期限切れフィルタあり）

        期待される動作:
        - 期限切れかつ未完了のタスクのみが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        overdue_tasks = repo.get_user_tasks(
            user_id=test_user.id,
            filters={"is_overdue": True}
        )

        # Assert（検証）
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].id == overdue_task.id
        assert overdue_tasks[0].due_date < datetime.now()
        assert overdue_tasks[0].status != TaskStatus.CLOSED

    def test_get_user_tasks_with_project_filter(
        self,
        db_session: Session,
        test_user: User,
        test_project: Project,
        sample_task: Task
    ):
        """
        ユーザータスク一覧取得をテスト（プロジェクトフィルタあり）

        期待される動作:
        - 指定されたプロジェクトのタスクのみが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        project_tasks = repo.get_user_tasks(
            user_id=test_user.id,
            filters={"project_id": test_project.id}
        )

        # Assert（検証）
        assert len(project_tasks) >= 1
        assert all(t.project_id == test_project.id for t in project_tasks)

    def test_get_overdue_tasks(
        self,
        db_session: Session,
        test_user: User,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        期限切れタスク取得をテスト

        期待される動作:
        - 期限切れかつ未完了のタスクが返される
        - 完了済みタスクは含まれない
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        overdue_tasks = repo.get_overdue_tasks()

        # Assert（検証）
        assert len(overdue_tasks) >= 1
        overdue_task_ids = [t.id for t in overdue_tasks]
        assert overdue_task.id in overdue_task_ids
        # 完了済みタスクは含まれない
        assert completed_task.id not in overdue_task_ids

    def test_get_overdue_tasks_by_user(
        self,
        db_session: Session,
        test_user: User,
        overdue_task: Task
    ):
        """
        期限切れタスク取得をテスト（ユーザー指定）

        期待される動作:
        - 指定されたユーザーの期限切れタスクのみが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        overdue_tasks = repo.get_overdue_tasks(user_id=test_user.id)

        # Assert（検証）
        assert len(overdue_tasks) >= 1
        assert all(t.assignee_id == test_user.id for t in overdue_tasks)

    def test_get_statistics_without_filters(
        self,
        db_session: Session,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        タスク統計取得をテスト（フィルタなし）

        期待される動作:
        - 全タスクの統計情報が返される
        - total_tasks、completed_tasks、in_progress_tasks、todo_tasksが正しい
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        stats = repo.get_statistics()

        # Assert（検証）
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 1
        assert stats["in_progress_tasks"] == 1
        assert stats["todo_tasks"] == 1
        assert stats["overdue_tasks"] == 1
        assert 0 <= stats["completion_rate"] <= 100

    def test_get_statistics_by_project(
        self,
        db_session: Session,
        test_project: Project,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        タスク統計取得をテスト（プロジェクト指定）

        期待される動作:
        - 指定されたプロジェクトの統計情報が返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        stats = repo.get_statistics(project_id=test_project.id)

        # Assert（検証）
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 1

    def test_get_statistics_by_user(
        self,
        db_session: Session,
        test_user: User,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        タスク統計取得をテスト（ユーザー指定）

        期待される動作:
        - 指定されたユーザーの統計情報が返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        stats = repo.get_statistics(user_id=test_user.id)

        # Assert（検証）
        assert stats["total_tasks"] == 3
        assert stats["completed_tasks"] == 1

    def test_get_recent_completed(
        self,
        db_session: Session,
        completed_task: Task
    ):
        """
        最近完了したタスク取得をテスト

        期待される動作:
        - 指定期間内に完了したタスクが返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        recent_completed = repo.get_recent_completed(days=7)

        # Assert（検証）
        assert len(recent_completed) >= 1
        completed_task_ids = [t.id for t in recent_completed]
        assert completed_task.id in completed_task_ids
        assert all(t.status == TaskStatus.CLOSED for t in recent_completed)

    def test_count_user_tasks(
        self,
        db_session: Session,
        test_user: User,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        ユーザータスク数カウントをテスト

        期待される動作:
        - ユーザーのタスク総数が返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        total_count = repo.count_user_tasks(user_id=test_user.id)
        todo_count = repo.count_user_tasks(
            user_id=test_user.id,
            status=TaskStatus.TODO
        )

        # Assert（検証）
        assert total_count == 3
        assert todo_count == 1

    def test_count_project_tasks(
        self,
        db_session: Session,
        test_project: Project,
        sample_task: Task,
        overdue_task: Task,
        completed_task: Task
    ):
        """
        プロジェクトタスク数カウントをテスト

        期待される動作:
        - プロジェクトのタスク総数が返される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        total_count = repo.count_project_tasks(project_id=test_project.id)
        closed_count = repo.count_project_tasks(
            project_id=test_project.id,
            status=TaskStatus.CLOSED
        )

        # Assert（検証）
        assert total_count == 3
        assert closed_count == 1

    def test_get_project_tasks_with_filters(
        self,
        db_session: Session,
        test_project: Project,
        sample_task: Task,
        overdue_task: Task
    ):
        """
        プロジェクトタスク一覧取得をテスト（フィルタあり）

        期待される動作:
        - 指定されたプロジェクトのタスクが返される
        - フィルタが正しく適用される
        """
        # Arrange（準備）
        repo = TaskRepository(db_session)

        # Act（実行）
        in_progress_tasks = repo.get_project_tasks(
            project_id=test_project.id,
            filters={"status": TaskStatus.IN_PROGRESS}
        )

        # Assert（検証）
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0].id == overdue_task.id
        assert in_progress_tasks[0].status == TaskStatus.IN_PROGRESS
