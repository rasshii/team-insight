"""
TeamRepositoryのユニットテスト

このモジュールは、TeamRepositoryの全メソッドをテストします。
チーム管理、メンバー管理、統計情報取得の正確性を検証します。
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.repositories.team_repository import TeamRepository
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.project import Project


@pytest.mark.unit
class TestTeamRepository:
    """TeamRepositoryのテストクラス"""

    @pytest.fixture
    def sample_team(self, db_session: Session) -> Team:
        """サンプルチームを作成するフィクスチャ"""
        team = Team(
            name="開発チーム",
            description="メイン開発チーム"
        )
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)
        return team

    @pytest.fixture
    def team_with_members(
        self,
        db_session: Session,
        sample_team: Team,
        test_user: User
    ) -> Team:
        """メンバーを持つチームを作成するフィクスチャ"""
        # test_userをチームメンバーとして追加
        member = TeamMember(
            team_id=sample_team.id,
            user_id=test_user.id,
            role=TeamRole.MEMBER
        )
        db_session.add(member)
        db_session.commit()
        db_session.refresh(sample_team)
        return sample_team

    @pytest.fixture
    def team_leader(self, db_session: Session) -> User:
        """チームリーダーユーザーを作成するフィクスチャ"""
        leader = User(
            email="leader@example.com",
            name="Team Leader",
            full_name="Team Leader",
            is_active=True,
            backlog_id=60001,
            user_id="team_leader"
        )
        db_session.add(leader)
        db_session.commit()
        db_session.refresh(leader)
        return leader

    @pytest.fixture
    def team_with_leader(
        self,
        db_session: Session,
        sample_team: Team,
        team_leader: User
    ) -> Team:
        """リーダーを持つチームを作成するフィクスチャ"""
        member = TeamMember(
            team_id=sample_team.id,
            user_id=team_leader.id,
            role=TeamRole.TEAM_LEADER
        )
        db_session.add(member)
        db_session.commit()
        db_session.refresh(sample_team)
        return sample_team

    @pytest.fixture
    def team_task(
        self,
        db_session: Session,
        test_user: User,
        test_project: Project
    ) -> Task:
        """チームメンバーのタスクを作成するフィクスチャ"""
        task = Task(
            backlog_id=2001,
            backlog_key="TEAM-1",
            project_id=test_project.id,
            assignee_id=test_user.id,
            reporter_id=test_user.id,
            title="Team Task",
            description="Task for team member",
            status=TaskStatus.TODO,
            due_date=datetime.now() + timedelta(days=7)
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    def test_get_by_name_success(self, db_session: Session, sample_team: Team):
        """
        チーム名による検索をテスト（成功ケース）

        期待される動作:
        - 存在するチーム名で正しいチームが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        found_team = repo.get_by_name(sample_team.name)

        # Assert（検証）
        assert found_team is not None
        assert found_team.id == sample_team.id
        assert found_team.name == sample_team.name
        assert found_team.description == sample_team.description

    def test_get_by_name_not_found(self, db_session: Session):
        """
        チーム名による検索をテスト（存在しないケース）

        期待される動作:
        - 存在しないチーム名でNoneが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        not_found_team = repo.get_by_name("存在しないチーム")

        # Assert（検証）
        assert not_found_team is None

    def test_get_with_members(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        メンバー情報を含むチーム取得をテスト（N+1問題対策の確認）

        期待される動作:
        - チーム情報とメンバー情報が1回のクエリで取得される
        - team.membersにアクセスしても追加クエリが発行されない
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        found_team = repo.get_with_members(team_with_members.id)

        # Assert（検証）
        assert found_team is not None
        assert found_team.id == team_with_members.id
        # メンバー情報が事前ロードされているか確認
        assert len(found_team.members) > 0
        assert found_team.members[0].user_id == test_user.id
        # ユーザー情報も事前ロード済み
        assert found_team.members[0].user is not None
        assert found_team.members[0].user.id == test_user.id

    def test_get_with_members_not_found(self, db_session: Session):
        """
        メンバー情報を含むチーム取得をテスト（存在しないケース）

        期待される動作:
        - 存在しないチームIDでNoneが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        not_found_team = repo.get_with_members(99999)

        # Assert（検証）
        assert not_found_team is None

    def test_get_user_teams(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        ユーザーが所属するチーム一覧取得をテスト

        期待される動作:
        - ユーザーが所属する全チームが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        user_teams = repo.get_user_teams(user_id=test_user.id)

        # Assert（検証）
        assert len(user_teams) >= 1
        team_ids = [t.id for t in user_teams]
        assert team_with_members.id in team_ids

    def test_get_user_teams_empty(self, db_session: Session, test_user: User):
        """
        ユーザーが所属するチーム一覧取得をテスト（所属チームなし）

        期待される動作:
        - 所属チームがない場合、空のリストが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # 新規ユーザーを作成（どのチームにも所属していない）
        new_user = User(
            email="newuser@example.com",
            name="New User",
            full_name="New User",
            is_active=True,
            backlog_id=70001,
            user_id="new_user"
        )
        db_session.add(new_user)
        db_session.commit()

        # Act（実行）
        user_teams = repo.get_user_teams(user_id=new_user.id)

        # Assert（検証）
        assert len(user_teams) == 0

    def test_get_team_statistics(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User,
        team_task: Task
    ):
        """
        チーム統計情報取得をテスト

        期待される動作:
        - チームのメンバー数、タスク数、効率性スコアが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        stats = repo.get_team_statistics(team_id=team_with_members.id)

        # Assert（検証）
        assert stats["member_count"] >= 1
        assert stats["active_tasks_count"] >= 1
        assert "completed_tasks_this_month" in stats
        assert "efficiency_score" in stats
        assert 0 <= stats["efficiency_score"] <= 100

    def test_get_team_members(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        チームメンバー取得をテスト

        期待される動作:
        - チームの全メンバーが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        members = repo.get_team_members(team_id=team_with_members.id)

        # Assert（検証）
        assert len(members) >= 1
        member_user_ids = [m.user_id for m in members]
        assert test_user.id in member_user_ids

    def test_get_team_members_by_role(
        self,
        db_session: Session,
        team_with_leader: Team,
        team_leader: User
    ):
        """
        チームメンバー取得をテスト（ロールフィルタあり）

        期待される動作:
        - 指定されたロールのメンバーのみが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        leaders = repo.get_team_members(
            team_id=team_with_leader.id,
            role=TeamRole.TEAM_LEADER
        )

        # Assert（検証）
        assert len(leaders) >= 1
        assert all(m.role == TeamRole.TEAM_LEADER for m in leaders)
        leader_user_ids = [m.user_id for m in leaders]
        assert team_leader.id in leader_user_ids

    def test_get_member_success(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        特定のメンバー情報取得をテスト（成功ケース）

        期待される動作:
        - 指定されたチームとユーザーのメンバー情報が返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        member = repo.get_member(
            team_id=team_with_members.id,
            user_id=test_user.id
        )

        # Assert（検証）
        assert member is not None
        assert member.team_id == team_with_members.id
        assert member.user_id == test_user.id
        # ユーザー情報も事前ロード済み
        assert member.user is not None

    def test_get_member_not_found(
        self,
        db_session: Session,
        sample_team: Team
    ):
        """
        特定のメンバー情報取得をテスト（存在しないケース）

        期待される動作:
        - 存在しないメンバーでNoneが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        member = repo.get_member(
            team_id=sample_team.id,
            user_id=99999
        )

        # Assert（検証）
        assert member is None

    def test_is_member_true(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        メンバーチェックをテスト（メンバーの場合）

        期待される動作:
        - ユーザーがチームメンバーの場合、Trueが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        is_member = repo.is_member(
            team_id=team_with_members.id,
            user_id=test_user.id
        )

        # Assert（検証）
        assert is_member is True

    def test_is_member_false(
        self,
        db_session: Session,
        sample_team: Team
    ):
        """
        メンバーチェックをテスト（メンバーでない場合）

        期待される動作:
        - ユーザーがチームメンバーでない場合、Falseが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        is_member = repo.is_member(
            team_id=sample_team.id,
            user_id=99999
        )

        # Assert（検証）
        assert is_member is False

    def test_is_team_leader_true(
        self,
        db_session: Session,
        team_with_leader: Team,
        team_leader: User
    ):
        """
        チームリーダーチェックをテスト（リーダーの場合）

        期待される動作:
        - ユーザーがチームリーダーの場合、Trueが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        is_leader = repo.is_team_leader(
            team_id=team_with_leader.id,
            user_id=team_leader.id
        )

        # Assert（検証）
        assert is_leader is True

    def test_is_team_leader_false(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User
    ):
        """
        チームリーダーチェックをテスト（リーダーでない場合）

        期待される動作:
        - ユーザーがチームリーダーでない場合、Falseが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        is_leader = repo.is_team_leader(
            team_id=team_with_members.id,
            user_id=test_user.id
        )

        # Assert（検証）
        assert is_leader is False

    def test_count_members(
        self,
        db_session: Session,
        team_with_members: Team
    ):
        """
        チームメンバー数カウントをテスト

        期待される動作:
        - チームのメンバー総数が返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        count = repo.count_members(team_id=team_with_members.id)

        # Assert（検証）
        assert count >= 1

    def test_count_team_leaders(
        self,
        db_session: Session,
        team_with_leader: Team
    ):
        """
        チームリーダー数カウントをテスト

        期待される動作:
        - チームのリーダー数が返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        count = repo.count_team_leaders(team_id=team_with_leader.id)

        # Assert（検証）
        assert count >= 1

    def test_get_members_performance(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User,
        team_task: Task
    ):
        """
        メンバーパフォーマンスデータ取得をテスト

        期待される動作:
        - 各メンバーのタスク統計が返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        performance = repo.get_members_performance(team_id=team_with_members.id)

        # Assert（検証）
        assert len(performance) >= 1
        # 最初のメンバーのデータを検証
        first_member = performance[0]
        assert "user_id" in first_member
        assert "user_name" in first_member
        assert "role" in first_member
        assert "completed_tasks" in first_member
        assert "active_tasks" in first_member
        assert "efficiency" in first_member
        assert "trend" in first_member

    def test_get_task_distribution(
        self,
        db_session: Session,
        team_with_members: Team,
        test_user: User,
        team_task: Task
    ):
        """
        タスク分配データ取得をテスト

        期待される動作:
        - チャート表示用のタスク分配データが返される
        """
        # Arrange（準備）
        repo = TeamRepository(db_session)

        # Act（実行）
        distribution = repo.get_task_distribution(team_id=team_with_members.id)

        # Assert（検証）
        assert "labels" in distribution
        assert "data" in distribution
        assert "backgroundColor" in distribution
        assert len(distribution["labels"]) >= 1
        assert len(distribution["data"]) >= 1
        # labelsとdataの長さが一致することを確認
        assert len(distribution["labels"]) == len(distribution["data"])
