import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.backlog_oauth import BacklogOAuthService
from app.models.auth import OAuthState
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.core.exceptions import ValidationException
from app.core.utils import QueryBuilder


class TestAuthService:
    """認証サービスのテスト"""

    @pytest.fixture
    def mock_backlog_oauth_service(self):
        return MagicMock(spec=BacklogOAuthService)

    @pytest.fixture
    def auth_service(self, mock_backlog_oauth_service):
        return AuthService(mock_backlog_oauth_service)

    @pytest.fixture
    def mock_db(self):
        db = MagicMock(spec=Session)
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        db.delete = MagicMock()
        db.flush = MagicMock()
        return db

    def test_validate_oauth_state_success(self, auth_service, mock_db):
        """有効なstateの検証が成功すること"""
        # モックデータの準備
        mock_state = MagicMock(spec=OAuthState)
        mock_state.state = "valid_state_123"
        mock_state.redirect_uri = "http://localhost:3000/auth/callback"
        mock_state.created_at = datetime.now(timezone.utc)
        mock_state.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        mock_state.is_expired.return_value = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state

        # テスト実行
        result = auth_service.validate_oauth_state(mock_db, "valid_state_123")

        # 検証
        assert result == mock_state
        mock_db.query.assert_called_once_with(OAuthState)

    def test_validate_oauth_state_not_found(self, auth_service, mock_db):
        """存在しないstateで例外が発生すること"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.all.return_value = []

        with pytest.raises(ValidationException) as exc_info:
            auth_service.validate_oauth_state(mock_db, "invalid_state")
        
        assert "無効なstateパラメータです" == exc_info.value.detail

    def test_validate_oauth_state_expired(self, auth_service, mock_db):
        """期限切れのstateで例外が発生すること"""
        mock_state = MagicMock(spec=OAuthState)
        mock_state.state = "expired_state"
        mock_state.redirect_uri = "http://localhost:3000/auth/callback"
        mock_state.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_state.expires_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        mock_state.is_expired.return_value = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_state

        with pytest.raises(ValidationException) as exc_info:
            auth_service.validate_oauth_state(mock_db, "expired_state")
        
        assert "stateパラメータの有効期限が切れています" == exc_info.value.detail
        mock_db.delete.assert_called_once_with(mock_state)
        mock_db.commit.assert_called_once()

    def test_extract_space_key_from_state_success(self, auth_service):
        """stateからspace_keyを正常に抽出できること"""
        import json
        import base64
        
        # stateデータの準備
        state_data = {"space_key": "test_space", "nonce": "12345"}
        state_json = json.dumps(state_data)
        state_encoded = base64.urlsafe_b64encode(state_json.encode()).decode()
        
        # テスト実行
        result = auth_service.extract_space_key_from_state(state_encoded)
        
        # 検証
        assert result == "test_space"

    def test_extract_space_key_from_state_fallback(self, auth_service):
        """stateのデコードに失敗した場合デフォルト値を返すこと"""
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.BACKLOG_SPACE_KEY = "default_space"
            
            # 無効なBase64文字列
            result = auth_service.extract_space_key_from_state("invalid_base64!!!")
            
            assert result == "default_space"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, auth_service, mock_backlog_oauth_service):
        """認証コードをトークンに交換できること"""
        mock_token_data = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        mock_backlog_oauth_service.exchange_code_for_token = AsyncMock(
            return_value=mock_token_data
        )
        
        result = await auth_service.exchange_code_for_token("auth_code_123", "test_space")
        
        assert result == mock_token_data
        mock_backlog_oauth_service.exchange_code_for_token.assert_called_once_with(
            "auth_code_123", space_key="test_space"
        )

    @pytest.mark.asyncio
    async def test_get_backlog_user_info(self, auth_service, mock_backlog_oauth_service):
        """Backlogユーザー情報を取得できること"""
        mock_user_info = {
            "id": 123,
            "userId": "testuser",
            "name": "テストユーザー",
            "mailAddress": "test@example.com"
        }
        mock_backlog_oauth_service.get_user_info = AsyncMock(
            return_value=mock_user_info
        )
        
        result = await auth_service.get_backlog_user_info("access_token", "test_space")
        
        assert result == mock_user_info
        mock_backlog_oauth_service.get_user_info.assert_called_once_with(
            "access_token", space_key="test_space"
        )

    def test_find_or_create_user_existing(self, auth_service, mock_db):
        """既存ユーザーの場合、情報を更新すること"""
        # 既存ユーザーのモック
        existing_user = User(
            id=1,
            backlog_id=123,
            email="old@example.com",
            name="古い名前",
            user_id="olduser"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        user_info = {
            "id": 123,
            "userId": "newuser",
            "name": "新しい名前",
            "mailAddress": "new@example.com"
        }
        
        result = auth_service.find_or_create_user(mock_db, user_info)
        
        # 検証
        assert result == existing_user
        assert result.email == "new@example.com"
        assert result.name == "新しい名前"
        assert result.user_id == "newuser"
        mock_db.commit.assert_called_once()

    def test_find_or_create_user_new(self, auth_service, mock_db):
        """新規ユーザーの場合、作成すること"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user_info = {
            "id": 456,
            "userId": "newuser",
            "name": "新規ユーザー",
            "mailAddress": "new@example.com"
        }
        
        # refreshメソッドの動作を設定
        def refresh_side_effect(user):
            user.id = 2  # 新規作成されたユーザーのIDを設定
        
        mock_db.refresh.side_effect = refresh_side_effect
        
        result = auth_service.find_or_create_user(mock_db, user_info)
        
        # 検証
        assert result.backlog_id == 456
        assert result.email == "new@example.com"
        assert result.name == "新規ユーザー"
        assert result.user_id == "newuser"
        assert result.is_active == True
        assert result.is_email_verified == True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_assign_default_role_if_needed_existing_role(self, auth_service, mock_db):
        """既にロールがある場合、そのまま返すこと"""
        # ロール付きユーザーのモック
        user_with_roles = User(id=1, user_roles=[UserRole()])
        
        mock_query = MagicMock()
        mock_query.first.return_value = user_with_roles
        
        with patch.object(QueryBuilder, 'with_user_roles', return_value=mock_query):
            result = auth_service.assign_default_role_if_needed(mock_db, user_with_roles)
            
            assert result == user_with_roles
            # 新しいロールは追加されない
            mock_db.add.assert_not_called()

    def test_assign_default_role_if_needed_new_role(self, auth_service, mock_db):
        """ロールがない場合、デフォルトロールを割り当てること"""
        # ロールなしユーザーのモック
        user_without_roles = User(id=1, user_roles=[])
        
        # MEMBERロールのモック
        member_role = Role(id=3, name="MEMBER")
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            member_role  # Role query
        ]
        
        # QueryBuilderのモック
        mock_query = MagicMock()
        mock_query.first.side_effect = [
            user_without_roles,  # 初回クエリ
            User(id=1, user_roles=[UserRole()])  # ロール追加後のクエリ
        ]
        
        with patch.object(QueryBuilder, 'with_user_roles', return_value=mock_query):
            result = auth_service.assign_default_role_if_needed(mock_db, user_without_roles)
            
            # UserRoleが作成されたことを確認
            mock_db.add.assert_called_once()
            added_user_role = mock_db.add.call_args[0][0]
            assert isinstance(added_user_role, UserRole)
            assert added_user_role.user_id == 1
            assert added_user_role.role_id == 3
            assert added_user_role.project_id is None
            
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_create_jwt_tokens(self, auth_service):
        """JWTトークンを生成できること"""
        with patch("app.services.auth_service.create_access_token") as mock_access_token, \
             patch("app.services.auth_service.create_refresh_token") as mock_refresh_token:
            
            mock_access_token.return_value = "access_token_123"
            mock_refresh_token.return_value = "refresh_token_456"
            
            access_token, refresh_token = auth_service.create_jwt_tokens(1)
            
            assert access_token == "access_token_123"
            assert refresh_token == "refresh_token_456"
            mock_access_token.assert_called_once_with(data={"sub": "1"})
            mock_refresh_token.assert_called_once_with(data={"sub": "1"})