# Team Insight バックエンドテストガイド

## テスト構成

```
tests/
├── unit/                 # 単体テスト
│   ├── test_security.py  # セキュリティ関数のテスト
│   ├── test_models.py    # モデルのバリデーションテスト
│   └── test_utils.py     # ユーティリティ関数のテスト
├── integration/          # 統合テスト
│   ├── test_auth_api.py  # 認証APIのテスト
│   ├── test_projects_api.py
│   └── test_database.py  # DB操作のテスト
├── feature/              # 機能テスト
│   ├── test_auth_flow.py # 認証フロー全体
│   └── test_project_management.py
├── examples/             # テストパターンの例（参考資料）
│   ├── config_test_patterns.py  # 設定テストのパターン例
│   └── mock_usage_patterns.py   # モック使用のパターン例
├── conftest.py           # 共通フィクスチャ
└── test_config.py        # 設定のテスト
```

## テスト作成のガイドライン

### 1. 単体テスト
- **対象**: 純粋な関数、ビジネスロジック
- **例**: パスワードハッシュ化、トークン生成、バリデーション

```python
# tests/unit/test_security.py
def test_verify_password():
    hashed = get_password_hash("testpassword")
    assert verify_password("testpassword", hashed) == True
    assert verify_password("wrongpassword", hashed) == False
```

### 2. 統合テスト
- **対象**: APIエンドポイント、DB操作
- **例**: CRUD操作、認証エンドポイント

```python
# tests/integration/test_auth_api.py
async def test_login_endpoint(client, test_user):
    response = await client.post("/api/v1/auth/login", json={
        "username": test_user.email,
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 3. 機能テスト
- **対象**: ユーザーストーリー全体
- **例**: プロジェクト作成から削除までの一連の流れ

```python
# tests/feature/test_project_management.py
async def test_project_lifecycle(client, auth_headers):
    # プロジェクト作成
    create_response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project"},
        headers=auth_headers
    )
    project_id = create_response.json()["id"]
    
    # プロジェクト更新
    update_response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Project"},
        headers=auth_headers
    )
    
    # プロジェクト削除
    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers=auth_headers
    )
```

## テスト実行

```bash
# 全テスト実行
pytest

# 単体テストのみ
pytest tests/unit/

# 特定のテストファイル
pytest tests/integration/test_auth_api.py

# 特定のテスト関数
pytest tests/unit/test_security.py::test_verify_password

# カバレッジ付き
pytest --cov=app --cov-report=html
```

## ベストプラクティス

1. **AAA パターン**
   - Arrange: テストデータの準備
   - Act: テスト対象の実行
   - Assert: 結果の検証

2. **テストの独立性**
   - 各テストは他のテストに依存しない
   - フィクスチャを使用してテストデータを準備

3. **命名規則**
   - テストファイル: `test_*.py`
   - テスト関数: `test_*`
   - 説明的な名前を使用

4. **パフォーマンス**
   - 単体テストは高速に（目標: 1テスト0.1秒以下）
   - 統合テストは必要最小限に
   - 機能テストは重要なフローのみ

## モックの使用ガイドライン

### モックを使うべき場合 🎭

```python
# 1. 外部API
@patch('requests.get')
def test_external_api_call(mock_get):
    mock_get.return_value.json.return_value = {"id": 1, "name": "Task"}
    result = fetch_external_task(1)
    assert result["name"] == "Task"

# 2. 時間依存の処理
@freeze_time("2024-01-01 12:00:00")
def test_token_expiration():
    token = create_access_token({"sub": "123"})
    # 時間が固定されているので安定したテスト

# 3. メール送信
@patch('app.services.email.send')
def test_send_notification(mock_send):
    mock_send.return_value = True
    result = send_welcome_email("user@example.com")
    assert result is True
```

### モックを使わない場合 🔨

```python
# 1. 設定・バリデーション
def test_validate_settings():
    test_settings = Settings(SECRET_KEY="test-key")
    result = validate_settings(test_settings)
    assert result is True

# 2. 統合テスト
async def test_create_user_integration(test_db):
    user = await user_repository.create(test_db, {"email": "test@example.com"})
    saved = await user_repository.get(test_db, user.id)
    assert saved.email == "test@example.com"

# 3. セキュリティ関連
def test_password_hashing():
    hashed = get_password_hash("password123")
    assert verify_password("password123", hashed) is True
```

### モック使用の判断基準

| 対象 | モック使用 | 理由 |
|------|-----------|------|
| 外部 API（HTTP） | ✅ 必須 | 外部サービス、レート制限、安定性 |
| データベース（単体テスト） | ✅ 推奨 | テスト速度、独立性 |
| データベース（統合テスト） | ❌ 使わない | 実際の動作確認が必要 |
| Redis（単体テスト） | ✅ 推奨 | テスト速度 |
| Redis（統合テスト） | ❌ 使わない | 実際のキャッシュ動作確認 |
| メール送信 | ✅ 必須 | 実際に送信してはいけない |
| ファイルシステム | 🔄 場合による | tmp_pathで十分な場合は不要 |
| 時間・日付 | ✅ 推奨 | テストの安定性 |
| ランダム値 | ✅ 推奨 | テストの再現性 |
| 設定検証 | ❌ 使わない | 実際のロジックをテスト |
| パスワードハッシュ | ❌ 使わない | セキュリティの正確性が重要 |

## テストの種類と範囲

### 正常系・異常系のバランス

```python
class TestUserAPI:
    # ✅ 正常系（40-50%）
    async def test_create_user_success(self):
        """ユーザー作成成功"""
        pass
    
    # ❌ 異常系（40-50%）
    async def test_create_user_invalid_email(self):
        """無効なメールアドレス"""
        pass
    
    async def test_create_user_duplicate_email(self):
        """重複するメールアドレス"""
        pass
    
    # 🔍 境界値（10-20%）
    async def test_create_user_email_max_length(self):
        """メールアドレスの最大長"""
        pass
```

### テストカバレッジの目標

- 全体: 80%以上
- コアビジネスロジック: 90%以上
- APIエンドポイント: 100%
- ユーティリティ関数: 70%以上

## フィクスチャの活用

```python
# conftest.py
@pytest.fixture
async def test_user(test_db):
    """テスト用ユーザー"""
    user = await create_user(test_db, {
        "email": "test@example.com",
        "name": "Test User"
    })
    yield user
    await delete_user(test_db, user.id)

@pytest.fixture
def mock_redis():
    """Redisクライアントのモック"""
    with patch('app.core.redis_client.redis_client') as mock:
        mock.get = Mock(return_value=None)
        mock.set = Mock(return_value=True)
        yield mock
```