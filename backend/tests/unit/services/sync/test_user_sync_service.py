"""
UserSyncServiceのユニットテスト

このモジュールは、UserSyncServiceの主要メソッドをテストします。
Backlog APIクライアントをモックして、ユーザーインポート処理の正確性を検証します。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.sync.user_sync_service import UserSyncService
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.core.permissions import RoleType


@pytest.mark.unit
class TestUserSyncService:
    """UserSyncServiceのテストクラス"""

    @pytest.fixture
    def user_sync_service(self):
        """UserSyncServiceインスタンスを作成するフィクスチャ"""
        return UserSyncService()

    @pytest.fixture
    def mock_backlog_projects(self):
        """モックBacklogプロジェクトデータ"""
        return [
            {
                "id": 1,
                "projectKey": "PROJ1",
                "name": "Project 1"
            },
            {
                "id": 2,
                "projectKey": "PROJ2",
                "name": "Project 2"
            }
        ]

    @pytest.fixture
    def mock_backlog_users(self):
        """モックBacklogユーザーデータ"""
        return [
            {
                "id": 101,
                "userId": "user1",
                "name": "User One",
                "mailAddress": "user1@example.com"
            },
            {
                "id": 102,
                "userId": "user2",
                "name": "User Two",
                "mailAddress": "user2@example.com"
            }
        ]

    @pytest.mark.asyncio
    async def test_import_users_from_backlog_success(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_projects,
        mock_backlog_users
    ):
        """
        Backlogからのユーザーインポートをテスト（成功ケース）

        期待される動作:
        - Backlog APIからプロジェクトとユーザーを取得
        - 新規ユーザーが作成される
        - デフォルトロールが付与される
        - 正しい結果が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # MEMBERロールを確認
        member_role = db_session.query(Role).filter(
            Role.name == RoleType.MEMBER
        ).first()
        assert member_role is not None

        # Backlog APIクライアントをモック
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            # モックの設定
            mock_client.get_projects = AsyncMock(return_value=mock_backlog_projects)
            mock_client.get_project_users = AsyncMock(return_value=mock_backlog_users)
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_users if u["userId"] == user_id
                )
            )

            # Act（実行）
            result = await user_sync_service.import_users_from_backlog(
                user=test_user,
                access_token=access_token,
                db=db_session,
                mode="active_only",
                assign_default_role=True
            )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 2  # 2名の新規ユーザー
        assert result["updated"] == 0
        assert result["total"] == 2
        assert result["projects_scanned"] == 2
        assert result["default_role_assigned"] is True

        # データベースに保存されたことを確認
        created_user = db_session.query(User).filter(
            User.backlog_id == 101
        ).first()
        assert created_user is not None
        assert created_user.name == "User One"
        assert created_user.email == "user1@example.com"
        assert created_user.is_active is True

        # デフォルトロールが付与されたことを確認
        user_role = db_session.query(UserRole).filter(
            UserRole.user_id == created_user.id,
            UserRole.project_id.is_(None)
        ).first()
        assert user_role is not None
        assert user_role.role_id == member_role.id

    @pytest.mark.asyncio
    async def test_import_users_from_backlog_update_existing(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_projects
    ):
        """
        Backlogからのユーザーインポートをテスト（既存ユーザー更新）

        期待される動作:
        - 既存ユーザーが更新される
        - created=0, updated=1が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # test_userと同じbacklog_idを持つユーザーデータ
        mock_existing_user = [{
            "id": test_user.backlog_id,
            "userId": test_user.user_id,
            "name": "Updated Name",
            "mailAddress": "updated@example.com"
        }]

        # Backlog APIクライアントをモック
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(return_value=mock_backlog_projects)
            mock_client.get_project_users = AsyncMock(return_value=mock_existing_user)
            mock_client.get_user_by_id = AsyncMock(return_value=mock_existing_user[0])

            # Act（実行）
            result = await user_sync_service.import_users_from_backlog(
                user=test_user,
                access_token=access_token,
                db=db_session,
                mode="active_only",
                assign_default_role=True
            )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 0
        assert result["updated"] == 1
        assert result["total"] == 1

        # ユーザー情報が更新されたことを確認
        db_session.refresh(test_user)
        assert test_user.name == "Updated Name"
        assert test_user.email == "updated@example.com"

    @pytest.mark.asyncio
    async def test_import_users_from_backlog_without_default_role(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_projects,
        mock_backlog_users
    ):
        """
        Backlogからのユーザーインポートをテスト（デフォルトロールなし）

        期待される動作:
        - デフォルトロールが付与されない
        - default_role_assigned=Falseが返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # Backlog APIクライアントをモック
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(return_value=mock_backlog_projects)
            mock_client.get_project_users = AsyncMock(return_value=mock_backlog_users)
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_users if u["userId"] == user_id
                )
            )

            # Act（実行）
            result = await user_sync_service.import_users_from_backlog(
                user=test_user,
                access_token=access_token,
                db=db_session,
                mode="active_only",
                assign_default_role=False  # デフォルトロールを付与しない
            )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 2
        assert result["default_role_assigned"] is False

        # ロールが付与されていないことを確認
        created_user = db_session.query(User).filter(
            User.backlog_id == 101
        ).first()
        user_roles = db_session.query(UserRole).filter(
            UserRole.user_id == created_user.id,
            UserRole.project_id.is_(None)
        ).all()
        assert len(user_roles) == 0

    @pytest.mark.asyncio
    async def test_import_users_from_backlog_duplicate_users(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_projects
    ):
        """
        Backlogからのユーザーインポートをテスト（重複ユーザー）

        期待される動作:
        - 複数のプロジェクトに所属する同一ユーザーは1回のみ処理される
        - total=ユニークユーザー数が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # 同じユーザーが複数のプロジェクトに所属
        duplicate_user = {
            "id": 201,
            "userId": "duplicate_user",
            "name": "Duplicate User",
            "mailAddress": "duplicate@example.com"
        }

        # Backlog APIクライアントをモック
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(return_value=mock_backlog_projects)
            # 両方のプロジェクトで同じユーザーを返す
            mock_client.get_project_users = AsyncMock(return_value=[duplicate_user])
            mock_client.get_user_by_id = AsyncMock(return_value=duplicate_user)

            # Act（実行）
            result = await user_sync_service.import_users_from_backlog(
                user=test_user,
                access_token=access_token,
                db=db_session,
                mode="active_only",
                assign_default_role=True
            )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 1  # 1名のみ作成
        assert result["total"] == 1  # ユニークユーザー数
        assert result["projects_scanned"] == 2  # 2つのプロジェクトを走査

        # データベースに1件のみ作成されたことを確認
        users = db_session.query(User).filter(
            User.backlog_id == 201
        ).all()
        assert len(users) == 1

    @pytest.mark.asyncio
    async def test_import_users_from_backlog_api_error(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User
    ):
        """
        Backlogからのユーザーインポートをテスト（APIエラー）

        期待される動作:
        - Backlog APIエラーが発生した場合、例外が発生する
        - 同期履歴が失敗として記録される
        """
        # Arrange（準備）
        access_token = "test_token"

        # Backlog APIクライアントをモック（エラーを発生させる）
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(
                side_effect=Exception("Backlog API Error")
            )

            # Act & Assert（実行・検証）
            with pytest.raises(Exception) as exc_info:
                await user_sync_service.import_users_from_backlog(
                    user=test_user,
                    access_token=access_token,
                    db=db_session,
                    mode="active_only",
                    assign_default_role=True
                )

            assert "Backlog API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_users_email_addresses_success(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User
    ):
        """
        ユーザーメールアドレス更新をテスト（成功ケース）

        期待される動作:
        - メールアドレス未設定のユーザーのメールアドレスが更新される
        """
        # Arrange（準備）
        access_token = "test_token"

        # メールアドレス未設定のユーザーを作成
        user_without_email = User(
            email=None,
            name="No Email User",
            full_name="No Email User",
            is_active=True,
            backlog_id=301,
            user_id="no_email_user"
        )
        db_session.add(user_without_email)
        db_session.commit()

        # Backlog APIクライアントをモック
        with patch("app.services.sync.user_sync_service.backlog_client") as mock_client:
            mock_client.get_user_by_id = AsyncMock(return_value={
                "id": 301,
                "userId": "no_email_user",
                "name": "No Email User",
                "mailAddress": "found@example.com"
            })

            # Act（実行）
            result = await user_sync_service.update_users_email_addresses(
                user=test_user,
                access_token=access_token,
                db=db_session
            )

        # Assert（検証）
        assert result["success"] is True
        assert result["updated"] == 1
        assert result["failed"] == 0
        assert result["total_without_email"] == 1

        # メールアドレスが更新されたことを確認
        db_session.refresh(user_without_email)
        assert user_without_email.email == "found@example.com"

    @pytest.mark.asyncio
    async def test_update_users_email_addresses_no_users(
        self,
        user_sync_service: UserSyncService,
        db_session: Session,
        test_user: User
    ):
        """
        ユーザーメールアドレス更新をテスト（対象ユーザーなし）

        期待される動作:
        - メールアドレス未設定のユーザーがいない場合、updated=0が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # Act（実行）
        result = await user_sync_service.update_users_email_addresses(
            user=test_user,
            access_token=access_token,
            db=db_session
        )

        # Assert（検証）
        assert result["success"] is True
        assert result["updated"] == 0
        assert result["total_without_email"] == 0
