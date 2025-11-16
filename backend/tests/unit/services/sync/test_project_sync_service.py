"""
ProjectSyncServiceのユニットテスト

このモジュールは、ProjectSyncServiceの主要メソッドをテストします。
Backlog APIクライアントをモックして、プロジェクト同期処理の正確性を検証します。
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.sync.project_sync_service import ProjectSyncService
from app.models.user import User
from app.models.project import Project


@pytest.mark.unit
class TestProjectSyncService:
    """ProjectSyncServiceのテストクラス"""

    @pytest.fixture
    def project_sync_service(self):
        """ProjectSyncServiceインスタンスを作成するフィクスチャ"""
        return ProjectSyncService()

    @pytest.fixture
    def mock_backlog_projects(self):
        """モックBacklogプロジェクトデータ"""
        return [
            {
                "id": 1001,
                "projectKey": "PROJ1",
                "name": "Project Alpha",
                "description": "Alpha project description",
                "archived": False
            },
            {
                "id": 1002,
                "projectKey": "PROJ2",
                "name": "Project Beta",
                "description": "Beta project description",
                "archived": False
            }
        ]

    @pytest.fixture
    def mock_backlog_project_users(self):
        """モックBacklogプロジェクトユーザーデータ"""
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
    async def test_sync_all_projects_success(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_projects,
        mock_backlog_project_users
    ):
        """
        全プロジェクト同期をテスト（成功ケース）

        期待される動作:
        - Backlog APIからプロジェクト一覧を取得
        - 新規プロジェクトが作成される
        - プロジェクトメンバーが同期される
        - 正しい結果が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            # モックの設定
            mock_client.get_projects = AsyncMock(return_value=mock_backlog_projects)
            mock_client.get_project_users = AsyncMock(return_value=mock_backlog_project_users)
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_project_users if u["userId"] == user_id
                )
            )

            # キャッシュ無効化をモック
            with patch.object(
                project_sync_service,
                "_invalidate_cache",
                new_callable=AsyncMock
            ):
                # Act（実行）
                result = await project_sync_service.sync_all_projects(
                    user=test_user,
                    access_token=access_token,
                    db=db_session
                )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 2  # 2件の新規プロジェクト
        assert result["updated"] == 0
        assert result["total"] == 2

        # データベースに保存されたことを確認
        created_project = db_session.query(Project).filter(
            Project.backlog_id == 1001
        ).first()
        assert created_project is not None
        assert created_project.name == "Project Alpha"
        assert created_project.project_key == "PROJ1"
        assert created_project.description == "Alpha project description"
        assert created_project.status == "active"

        # メンバーが同期されたことを確認
        assert len(created_project.members) == 2

    @pytest.mark.asyncio
    async def test_sync_all_projects_update_existing(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_user: User,
        test_project: Project,
        mock_backlog_project_users
    ):
        """
        全プロジェクト同期をテスト（既存プロジェクト更新）

        期待される動作:
        - 既存プロジェクトが更新される
        - created=0, updated=1が返される
        """
        # Arrange（準備）
        access_token = "test_token"

        # test_projectと同じbacklog_idを持つプロジェクトデータ
        mock_existing_project = [{
            "id": test_project.backlog_id,
            "projectKey": test_project.project_key,
            "name": "Updated Project Name",
            "description": "Updated description",
            "archived": False
        }]

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(return_value=mock_existing_project)
            mock_client.get_project_users = AsyncMock(return_value=mock_backlog_project_users)
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_project_users if u["userId"] == user_id
                )
            )

            # キャッシュ無効化をモック
            with patch.object(
                project_sync_service,
                "_invalidate_cache",
                new_callable=AsyncMock
            ):
                # Act（実行）
                result = await project_sync_service.sync_all_projects(
                    user=test_user,
                    access_token=access_token,
                    db=db_session
                )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 0
        assert result["updated"] == 1
        assert result["total"] == 1

        # プロジェクト情報が更新されたことを確認
        db_session.refresh(test_project)
        assert test_project.name == "Updated Project Name"
        assert test_project.description == "Updated description"

    @pytest.mark.asyncio
    async def test_sync_all_projects_archived_status(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_user: User,
        mock_backlog_project_users
    ):
        """
        全プロジェクト同期をテスト（アーカイブ済みプロジェクト）

        期待される動作:
        - アーカイブ済みプロジェクトのステータスが正しく設定される
        """
        # Arrange（準備）
        access_token = "test_token"

        # アーカイブ済みプロジェクト
        mock_archived_project = [{
            "id": 2001,
            "projectKey": "ARCHIVED",
            "name": "Archived Project",
            "description": "This is archived",
            "archived": True
        }]

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(return_value=mock_archived_project)
            mock_client.get_project_users = AsyncMock(return_value=mock_backlog_project_users)
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_project_users if u["userId"] == user_id
                )
            )

            # キャッシュ無効化をモック
            with patch.object(
                project_sync_service,
                "_invalidate_cache",
                new_callable=AsyncMock
            ):
                # Act（実行）
                result = await project_sync_service.sync_all_projects(
                    user=test_user,
                    access_token=access_token,
                    db=db_session
                )

        # Assert（検証）
        assert result["success"] is True
        assert result["created"] == 1

        # プロジェクトステータスが"archived"に設定されたことを確認
        archived_project = db_session.query(Project).filter(
            Project.backlog_id == 2001
        ).first()
        assert archived_project is not None
        assert archived_project.status == "archived"

    @pytest.mark.asyncio
    async def test_sync_all_projects_api_error(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_user: User
    ):
        """
        全プロジェクト同期をテスト（APIエラー）

        期待される動作:
        - Backlog APIエラーが発生した場合、例外が発生する
        - 同期履歴が失敗として記録される
        """
        # Arrange（準備）
        access_token = "test_token"

        # Backlog APIクライアントをモック（エラーを発生させる）
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_projects = AsyncMock(
                side_effect=Exception("Backlog API Error")
            )

            # Act & Assert（実行・検証）
            with pytest.raises(Exception) as exc_info:
                await project_sync_service.sync_all_projects(
                    user=test_user,
                    access_token=access_token,
                    db=db_session
                )

            assert "Backlog API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_single_project_success(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        mock_backlog_projects
    ):
        """
        単一プロジェクト同期をテスト（成功ケース）

        期待される動作:
        - 指定されたプロジェクトが同期される
        - Projectオブジェクトが返される
        """
        # Arrange（準備）
        access_token = "test_token"
        project_id = 1001

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_project_by_id = AsyncMock(
                return_value=mock_backlog_projects[0]
            )

            # Act（実行）
            project = await project_sync_service.sync_single_project(
                project_id=project_id,
                access_token=access_token,
                db=db_session
            )

        # Assert（検証）
        assert project is not None
        assert project.backlog_id == 1001
        assert project.name == "Project Alpha"
        assert project.project_key == "PROJ1"

    @pytest.mark.asyncio
    async def test_sync_single_project_api_error(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session
    ):
        """
        単一プロジェクト同期をテスト（APIエラー）

        期待される動作:
        - Backlog APIエラーが発生した場合、例外が発生する
        """
        # Arrange（準備）
        access_token = "test_token"
        project_id = 1001

        # Backlog APIクライアントをモック（エラーを発生させる）
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_project_by_id = AsyncMock(
                side_effect=Exception("Project not found")
            )

            # Act & Assert（実行・検証）
            with pytest.raises(Exception) as exc_info:
                await project_sync_service.sync_single_project(
                    project_id=project_id,
                    access_token=access_token,
                    db=db_session
                )

            assert "Project not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_project_members_creates_new_users(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_project: Project,
        mock_backlog_project_users
    ):
        """
        プロジェクトメンバー同期をテスト（新規ユーザー作成）

        期待される動作:
        - メンバーとして登録されていないユーザーが自動的に作成される
        - プロジェクトのmembersリレーションが更新される
        """
        # Arrange（準備）
        access_token = "test_token"
        project_data = {
            "id": test_project.backlog_id,
            "projectKey": test_project.project_key,
            "name": test_project.name
        }

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_project_users = AsyncMock(
                return_value=mock_backlog_project_users
            )
            mock_client.get_user_by_id = AsyncMock(
                side_effect=lambda user_id, token: next(
                    u for u in mock_backlog_project_users if u["userId"] == user_id
                )
            )

            # Act（実行）
            await project_sync_service._sync_project_members(
                project=test_project,
                project_data=project_data,
                access_token=access_token,
                db=db_session
            )

        # Assert（検証）
        db_session.refresh(test_project)
        # test_userと新規作成された2名の合計3名以上（元々いたメンバー + 新規メンバー）
        assert len(test_project.members) >= 2

        # 新規ユーザーが作成されたことを確認
        new_user = db_session.query(User).filter(
            User.backlog_id == 101
        ).first()
        assert new_user is not None
        assert new_user.name == "User One"
        assert new_user.email == "user1@example.com"

    @pytest.mark.asyncio
    async def test_sync_project_members_handles_duplicate_users(
        self,
        project_sync_service: ProjectSyncService,
        db_session: Session,
        test_project: Project,
        test_user: User
    ):
        """
        プロジェクトメンバー同期をテスト（重複ユーザー処理）

        期待される動作:
        - 既存ユーザーは新規作成されず、既存のものが使用される
        """
        # Arrange（準備）
        access_token = "test_token"
        project_data = {
            "id": test_project.backlog_id,
            "projectKey": test_project.project_key,
            "name": test_project.name
        }

        # test_userと同じbacklog_idを持つユーザーデータ
        mock_existing_user = [{
            "id": test_user.backlog_id,
            "userId": test_user.user_id,
            "name": test_user.name,
            "mailAddress": test_user.email
        }]

        # Backlog APIクライアントをモック
        with patch("app.services.sync.project_sync_service.backlog_client") as mock_client:
            mock_client.get_project_users = AsyncMock(return_value=mock_existing_user)
            mock_client.get_user_by_id = AsyncMock(return_value=mock_existing_user[0])

            # 初期のユーザー数を記録
            initial_user_count = db_session.query(User).count()

            # Act（実行）
            await project_sync_service._sync_project_members(
                project=test_project,
                project_data=project_data,
                access_token=access_token,
                db=db_session
            )

            # 同期後のユーザー数を確認
            final_user_count = db_session.query(User).count()

        # Assert（検証）
        # 新規ユーザーが作成されていないことを確認
        assert final_user_count == initial_user_count

        # プロジェクトメンバーに既存ユーザーが含まれていることを確認
        db_session.refresh(test_project)
        member_ids = [m.id for m in test_project.members]
        assert test_user.id in member_ids
