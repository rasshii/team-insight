"""
設定テストの正常系・異常系の例
"""
import pytest
from app.core.config import Settings, validate_settings


class TestValidateSettings:
    """validate_settings関数のテスト例"""
    
    # ========== 正常系テスト ==========
    
    def test_validate_settings_valid_production(self):
        """✅ 正常系: 本番環境で全て適切な設定の場合"""
        test_settings = Settings(
            SECRET_KEY="production-secret-key-abc123xyz",
            DATABASE_URL="postgresql://produser:prodpass@db.example.com:5432/team_insight",
            REDISCLI_AUTH="production-redis-password",
            BACKLOG_CLIENT_ID="prod-client-id",
            BACKLOG_CLIENT_SECRET="prod-client-secret",
            BACKLOG_SPACE_KEY="prod-space",
            DEBUG=False,
        )
        
        # 検証が成功することを確認
        result = validate_settings()
        assert result == True
    
    def test_validate_settings_valid_development(self):
        """✅ 正常系: 開発環境でデフォルト値を使用している場合"""
        test_settings = Settings(
            SECRET_KEY="your-secret-key-here",  # デフォルト値
            DEBUG=True,  # 開発モード
            BACKLOG_CLIENT_ID="dev-client-id",
            BACKLOG_CLIENT_SECRET="dev-client-secret",
            BACKLOG_SPACE_KEY="dev-space",
        )
        
        # 開発環境では警告は出るが、検証は失敗しない
        result = validate_settings()
        assert result == False  # 警告があるのでFalse
    
    # ========== 異常系テスト ==========
    
    def test_validate_settings_missing_backlog_config(self):
        """❌ 異常系: Backlog設定が不足している場合"""
        test_settings = Settings(
            SECRET_KEY="good-secret-key",
            BACKLOG_CLIENT_ID="",  # 空
            BACKLOG_CLIENT_SECRET="",  # 空
            BACKLOG_SPACE_KEY="",  # 空
            DEBUG=True,
        )
        
        result = validate_settings()
        assert result == False
        # エラーメッセージが出力されることも確認
    
    def test_validate_settings_production_with_defaults(self):
        """❌ 異常系: 本番環境でデフォルト値を使用している場合"""
        test_settings = Settings(
            SECRET_KEY="your-secret-key-here",  # デフォルト値
            DATABASE_URL="postgresql://localhost:5432/team_insight",  # localhost
            REDISCLI_AUTH="redis_password",  # デフォルト値
            DEBUG=False,  # 本番モード
        )
        
        result = validate_settings()
        assert result == False
        # 本番環境では必ずエラーになることを確認
    
    # ========== 境界値テスト ==========
    
    def test_validate_settings_empty_strings(self):
        """🔍 境界値: 空文字列の場合"""
        test_settings = Settings(
            SECRET_KEY="",  # 空文字列
            BACKLOG_CLIENT_ID="",
            BACKLOG_CLIENT_SECRET="",
            BACKLOG_SPACE_KEY="",
        )
        
        result = validate_settings()
        assert result == False
    
    def test_validate_settings_none_values(self):
        """🔍 境界値: None値の場合（設定可能な場合）"""
        # 環境変数が設定されていない場合のテスト
        pass


class TestPasswordValidation:
    """パスワードバリデーションのテスト例"""
    
    # ========== 正常系 ==========
    
    def test_valid_password(self):
        """✅ 正常系: 全ての要件を満たすパスワード"""
        password = "MyStr0ng!Pass"
        assert validate_password(password) == True
    
    def test_valid_password_minimum_length(self):
        """✅ 正常系: 最小長のパスワード"""
        password = "Ab1!efgh"  # 8文字
        assert validate_password(password) == True
    
    # ========== 異常系 ==========
    
    def test_password_too_short(self):
        """❌ 異常系: パスワードが短すぎる"""
        password = "Ab1!"  # 4文字
        assert validate_password(password) == False
    
    def test_password_no_uppercase(self):
        """❌ 異常系: 大文字がない"""
        password = "mystr0ng!pass"
        assert validate_password(password) == False
    
    def test_password_no_lowercase(self):
        """❌ 異常系: 小文字がない"""
        password = "MYSTR0NG!PASS"
        assert validate_password(password) == False
    
    def test_password_no_numbers(self):
        """❌ 異常系: 数字がない"""
        password = "MyStrong!Pass"
        assert validate_password(password) == False
    
    def test_password_no_special(self):
        """❌ 異常系: 特殊文字がない"""
        password = "MyStr0ngPass"
        assert validate_password(password) == False
    
    # ========== 境界値テスト ==========
    
    def test_password_exactly_minimum_length(self):
        """🔍 境界値: ちょうど最小長"""
        password = "Ab1!efg"  # 7文字（最小8文字なので失敗すべき）
        assert validate_password(password) == False
        
        password = "Ab1!efgh"  # 8文字（最小値）
        assert validate_password(password) == True
    
    def test_password_special_characters(self):
        """🔍 境界値: 様々な特殊文字"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"MyPass1{char}"
            assert validate_password(password) == True
    
    def test_password_unicode(self):
        """🔍 境界値: Unicode文字"""
        password = "MyPass1!あ"  # 日本語を含む
        # 仕様によってTrueまたはFalse
        result = validate_password(password)
        assert isinstance(result, bool)
    
    # ========== セキュリティテスト ==========
    
    def test_common_passwords(self):
        """🔒 セキュリティ: よくあるパスワード"""
        common_passwords = [
            "Password1!",
            "Admin123!",
            "Qwerty123!",
        ]
        for password in common_passwords:
            # よくあるパスワードは拒否されるべき（実装による）
            result = validate_password(password, check_common=True)
            # 実装次第


class TestAPIEndpoint:
    """APIエンドポイントのテスト例"""
    
    # ========== 正常系 ==========
    
    async def test_create_user_success(self, client):
        """✅ 正常系: ユーザー作成成功"""
        response = await client.post("/api/v1/users", json={
            "email": "test@example.com",
            "password": "ValidPass123!",
            "name": "Test User"
        })
        assert response.status_code == 201
        assert response.json()["email"] == "test@example.com"
    
    # ========== 異常系 ==========
    
    async def test_create_user_invalid_email(self, client):
        """❌ 異常系: 無効なメールアドレス"""
        response = await client.post("/api/v1/users", json={
            "email": "invalid-email",
            "password": "ValidPass123!",
            "name": "Test User"
        })
        assert response.status_code == 422
        assert "email" in response.json()["detail"][0]["loc"]
    
    async def test_create_user_duplicate_email(self, client, existing_user):
        """❌ 異常系: 重複するメールアドレス"""
        response = await client.post("/api/v1/users", json={
            "email": existing_user.email,  # 既存のメール
            "password": "ValidPass123!",
            "name": "Another User"
        })
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    async def test_create_user_missing_fields(self, client):
        """❌ 異常系: 必須フィールドが不足"""
        response = await client.post("/api/v1/users", json={
            "email": "test@example.com",
            # passwordが不足
        })
        assert response.status_code == 422
    
    # ========== 境界値テスト ==========
    
    async def test_create_user_empty_name(self, client):
        """🔍 境界値: 名前が空文字"""
        response = await client.post("/api/v1/users", json={
            "email": "test@example.com",
            "password": "ValidPass123!",
            "name": ""  # 空文字
        })
        # 仕様による（許可するか、エラーとするか）
        assert response.status_code in [201, 422]
    
    # ========== 認証・認可テスト ==========
    
    async def test_access_without_auth(self, client):
        """🔒 認証: 認証なしでのアクセス"""
        response = await client.get("/api/v1/protected")
        assert response.status_code == 401
    
    async def test_access_with_invalid_token(self, client):
        """🔒 認証: 無効なトークンでのアクセス"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await client.get("/api/v1/protected", headers=headers)
        assert response.status_code == 401
    
    async def test_access_without_permission(self, client, regular_user_token):
        """🔒 認可: 権限不足でのアクセス"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = await client.delete("/api/v1/admin/users/1", headers=headers)
        assert response.status_code == 403  # Forbidden