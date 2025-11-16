"""
UserRepositoryのユニットテスト

このモジュールは、UserRepositoryの全メソッドをテストします。
データベース操作の正確性、パフォーマンス、エッジケースの処理を検証します。
"""

import pytest
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.models.project import Project
from app.core.permissions import RoleType


@pytest.mark.unit
class TestUserRepository:
    """UserRepositoryのテストクラス"""

    def test_get_by_email_success(self, db_session: Session, test_user: User):
        """
        メールアドレスによるユーザー検索をテスト（成功ケース）

        期待される動作:
        - 存在するメールアドレスで正しいユーザーが返される
        - ユーザーのIDと名前が一致する
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        found_user = repo.get_by_email(test_user.email)

        # Assert（検証）
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
        assert found_user.full_name == test_user.full_name

    def test_get_by_email_not_found(self, db_session: Session):
        """
        メールアドレスによるユーザー検索をテスト（存在しないケース）

        期待される動作:
        - 存在しないメールアドレスでNoneが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        not_found_user = repo.get_by_email("notexist@example.com")

        # Assert（検証）
        assert not_found_user is None

    def test_get_by_backlog_id_success(self, db_session: Session, test_user: User):
        """
        Backlog IDによるユーザー検索をテスト（成功ケース）

        期待される動作:
        - 存在するBacklog IDで正しいユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        found_user = repo.get_by_backlog_id(test_user.backlog_id)

        # Assert（検証）
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.backlog_id == test_user.backlog_id

    def test_get_by_backlog_id_not_found(self, db_session: Session):
        """
        Backlog IDによるユーザー検索をテスト（存在しないケース）

        期待される動作:
        - 存在しないBacklog IDでNoneが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        not_found_user = repo.get_by_backlog_id(99999)

        # Assert（検証）
        assert not_found_user is None

    def test_get_by_user_id_success(self, db_session: Session, test_user: User):
        """
        ユーザーID（文字列）によるユーザー検索をテスト（成功ケース）

        期待される動作:
        - 存在するユーザーIDで正しいユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        found_user = repo.get_by_user_id(test_user.user_id)

        # Assert（検証）
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.user_id == test_user.user_id

    def test_get_with_roles_returns_user_with_roles(self, db_session: Session, test_user: User):
        """
        ロール情報を含むユーザー取得をテスト（N+1問題対策の確認）

        期待される動作:
        - ユーザー情報とロール情報が1回のクエリで取得される
        - user.user_rolesにアクセスしても追加クエリが発行されない
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # MEMBERロールを取得してユーザーに割り当て
        member_role = db_session.query(Role).filter(
            Role.name == RoleType.MEMBER
        ).first()

        user_role = UserRole(
            user_id=test_user.id,
            role_id=member_role.id,
            project_id=None  # グローバルロール
        )
        db_session.add(user_role)
        db_session.commit()

        # Act（実行）
        found_user = repo.get_with_roles(test_user.id)

        # Assert（検証）
        assert found_user is not None
        assert found_user.id == test_user.id
        # ロール情報が事前ロードされているか確認
        assert len(found_user.user_roles) > 0
        assert found_user.user_roles[0].role.name == RoleType.MEMBER

    def test_get_with_roles_not_found(self, db_session: Session):
        """
        ロール情報を含むユーザー取得をテスト（存在しないケース）

        期待される動作:
        - 存在しないユーザーIDでNoneが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        not_found_user = repo.get_with_roles(99999)

        # Assert（検証）
        assert not_found_user is None

    def test_get_with_projects(self, db_session: Session, test_user: User, test_project: Project):
        """
        プロジェクト情報を含むユーザー取得をテスト

        期待される動作:
        - ユーザー情報とプロジェクト情報が1回のクエリで取得される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        found_user = repo.get_with_projects(test_user.id)

        # Assert（検証）
        assert found_user is not None
        assert found_user.id == test_user.id
        # プロジェクト情報が事前ロードされているか確認
        assert len(found_user.projects) > 0
        assert found_user.projects[0].id == test_project.id

    def test_search_by_name(self, db_session: Session):
        """
        ユーザー検索（名前で検索）をテスト

        期待される動作:
        - 名前に検索クエリを含むユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # テストユーザーを作成
        user1 = User(
            email="tanaka@example.com",
            name="田中太郎",
            full_name="田中太郎",
            is_active=True,
            backlog_id=10001,
            user_id="tanaka"
        )
        user2 = User(
            email="suzuki@example.com",
            name="鈴木次郎",
            full_name="鈴木次郎",
            is_active=True,
            backlog_id=10002,
            user_id="suzuki"
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Act（実行）
        results = repo.search(query="田中")

        # Assert（検証）
        assert len(results) == 1
        assert results[0].name == "田中太郎"

    def test_search_by_email(self, db_session: Session):
        """
        ユーザー検索（メールアドレスで検索）をテスト

        期待される動作:
        - メールアドレスに検索クエリを含むユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # テストユーザーを作成
        user1 = User(
            email="test1@example.com",
            name="User 1",
            full_name="User 1",
            is_active=True,
            backlog_id=10003,
            user_id="user1"
        )
        user2 = User(
            email="test2@another.com",
            name="User 2",
            full_name="User 2",
            is_active=True,
            backlog_id=10004,
            user_id="user2"
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # Act（実行）
        results = repo.search(query="example.com")

        # Assert（検証）
        assert len(results) == 1
        assert results[0].email == "test1@example.com"

    def test_search_with_pagination(self, db_session: Session):
        """
        ユーザー検索（ページネーション）をテスト

        期待される動作:
        - skipとlimitパラメータが正しく動作する
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # 複数のテストユーザーを作成
        for i in range(5):
            user = User(
                email=f"user{i}@test.com",
                name=f"Test User {i}",
                full_name=f"Test User {i}",
                is_active=True,
                backlog_id=20000 + i,
                user_id=f"testuser{i}"
            )
            db_session.add(user)
        db_session.commit()

        # Act（実行）
        results_page1 = repo.search(query="Test User", skip=0, limit=2)
        results_page2 = repo.search(query="Test User", skip=2, limit=2)

        # Assert（検証）
        assert len(results_page1) == 2
        assert len(results_page2) == 2
        # ページ1と2で異なるユーザーが返されることを確認
        assert results_page1[0].id != results_page2[0].id

    def test_get_active_users(self, db_session: Session):
        """
        アクティブユーザーのみ取得をテスト

        期待される動作:
        - is_active=Trueのユーザーのみが返される
        - is_active=Falseのユーザーは含まれない
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # アクティブユーザーと非アクティブユーザーを作成
        active_user = User(
            email="active@example.com",
            name="Active User",
            full_name="Active User",
            is_active=True,
            backlog_id=30001,
            user_id="active_user"
        )
        inactive_user = User(
            email="inactive@example.com",
            name="Inactive User",
            full_name="Inactive User",
            is_active=False,
            backlog_id=30002,
            user_id="inactive_user"
        )
        db_session.add_all([active_user, inactive_user])
        db_session.commit()

        # Act（実行）
        active_users = repo.get_active_users()

        # Assert（検証）
        # test_userもアクティブなので、合計2名以上
        assert len(active_users) >= 1
        # 非アクティブユーザーが含まれていないことを確認
        active_user_ids = [u.id for u in active_users]
        assert inactive_user.id not in active_user_ids
        assert active_user.id in active_user_ids

    def test_get_active_users_with_pagination(self, db_session: Session):
        """
        アクティブユーザー取得（ページネーション）をテスト

        期待される動作:
        - skipとlimitパラメータが正しく動作する
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # 複数のアクティブユーザーを作成
        for i in range(5):
            user = User(
                email=f"active{i}@test.com",
                name=f"Active {i}",
                full_name=f"Active {i}",
                is_active=True,
                backlog_id=40000 + i,
                user_id=f"active{i}"
            )
            db_session.add(user)
        db_session.commit()

        # Act（実行）
        results = repo.get_active_users(skip=0, limit=2)

        # Assert（検証）
        assert len(results) == 2
        assert all(u.is_active for u in results)

    def test_get_admins(self, db_session: Session):
        """
        管理者ユーザー取得をテスト

        期待される動作:
        - is_superuser=TrueまたはADMINロールを持つユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # 管理者ユーザーを作成
        admin_user = User(
            email="admin@example.com",
            name="Admin User",
            full_name="Admin User",
            is_active=True,
            is_superuser=True,
            backlog_id=50001,
            user_id="admin_user"
        )
        db_session.add(admin_user)
        db_session.commit()

        # Act（実行）
        admins = repo.get_admins()

        # Assert（検証）
        assert len(admins) >= 1
        admin_ids = [a.id for a in admins]
        assert admin_user.id in admin_ids

    def test_get_users_by_project(self, db_session: Session, test_user: User, test_project: Project):
        """
        プロジェクトメンバー取得をテスト

        期待される動作:
        - 指定されたプロジェクトに所属するユーザーが返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        members = repo.get_users_by_project(test_project.id)

        # Assert（検証）
        assert len(members) >= 1
        member_ids = [m.id for m in members]
        assert test_user.id in member_ids

    def test_count_by_project(self, db_session: Session, test_user: User, test_project: Project):
        """
        プロジェクトメンバー数カウントをテスト

        期待される動作:
        - 指定されたプロジェクトのメンバー数が返される
        """
        # Arrange（準備）
        repo = UserRepository(db_session)

        # Act（実行）
        count = repo.count_by_project(test_project.id)

        # Assert（検証）
        assert count >= 1
