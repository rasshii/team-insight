# 同期サービス - リファクタリング概要

## 概要

このディレクトリには、Backlogからデータを同期する機能を提供するサービスが含まれています。
887行の巨大な`sync_service.py`を単一責任原則に基づいて分割し、保守性とテスタビリティを向上させました。

## ファイル構成

### 1. base_sync_service.py (308行)
**責任**: 共通機能を提供する基底クラス

**主な機能**:
- 同期履歴の作成・管理
- ユーザーの取得または作成
- 日付文字列のパース
- エラーハンドリング
- キャッシュ無効化

**使用例**:
```python
class UserSyncService(BaseSyncService):
    async def sync_users(self, ...):
        # 基底クラスのメソッドを利用
        sync_history = self._create_sync_history(...)
        user = self._get_or_create_user(...)
```

### 2. user_sync_service.py (539行)
**責任**: ユーザー情報の同期

**主な機能**:
- Backlogから全プロジェクトのユーザーをインポート
- ユーザー情報の更新
- メールアドレスの更新
- デフォルトロールの自動付与

**使用例**:
```python
from app.services.sync import user_sync_service

result = await user_sync_service.import_users_from_backlog(
    user=current_user,
    access_token=token,
    db=db,
    mode="active_only",
    assign_default_role=True
)
```

### 3. project_sync_service.py (444行)
**責任**: プロジェクト情報の同期

**主な機能**:
- 全プロジェクトの同期
- 単一プロジェクトの同期
- プロジェクトメンバーの同期
- 同期後のキャッシュ無効化

**使用例**:
```python
from app.services.sync import project_sync_service

result = await project_sync_service.sync_all_projects(
    user=current_user,
    access_token=token,
    db=db
)
```

### 4. task_sync_service.py (619行)
**責任**: タスク（課題）情報の同期

**主な機能**:
- ユーザータスクの同期
- プロジェクトタスクの同期
- 単一タスクの同期
- タスクデータの変換（BacklogのIssue -> 内部のTask）
- 同期状況の取得

**使用例**:
```python
from app.services.sync import task_sync_service

result = await task_sync_service.sync_user_tasks(
    user=current_user,
    access_token=token,
    db=db,
    project_id=None  # 全プロジェクトのタスク
)
```

### 5. integrated_sync_service.py (384行)
**責任**: 後方互換性のための統合サービス

**主な機能**:
- 既存のインターフェースを維持
- 分割されたサービスを内部で呼び出す
- 接続状態の確認

**使用例**:
```python
# 既存のコード（変更不要）
from app.services.sync_service import sync_service

result = await sync_service.sync_user_tasks(user, token, db)
result = await sync_service.sync_all_projects(user, token, db)
```

### 6. __init__.py (66行)
**責任**: パッケージのエクスポート

**エクスポート内容**:
- `user_sync_service`: ユーザー同期サービスのインスタンス
- `project_sync_service`: プロジェクト同期サービスのインスタンス
- `task_sync_service`: タスク同期サービスのインスタンス
- `sync_service`: 統合サービスのインスタンス（後方互換性）

## 設計原則

### 1. 単一責任原則 (Single Responsibility Principle)
各サービスは特定の同期機能のみを担当します：
- `UserSyncService`: ユーザー同期のみ
- `ProjectSyncService`: プロジェクト同期のみ
- `TaskSyncService`: タスク同期のみ

### 2. DRY原則 (Don't Repeat Yourself)
共通機能は`BaseSyncService`で実装し、各サービスで再利用します：
- 同期履歴の作成
- ユーザーの作成
- 日付のパース
- エラーハンドリング

### 3. 依存性注入 (Dependency Injection)
データベースセッションやアクセストークンを外部から注入します：
```python
async def sync_users(self, user: User, access_token: str, db: Session):
    # 外部から注入されたパラメータを使用
```

### 4. テスタビリティ
各サービスを独立してテスト可能な構造にしました：
```python
# ユーザー同期のユニットテスト
async def test_import_users_from_backlog():
    result = await user_sync_service.import_users_from_backlog(...)
    assert result["success"] == True
```

## 後方互換性

既存のコードを壊さないために、以下の措置を講じました：

### 1. sync_service.py（29行）
元の`sync_service.py`は、新しい`integrated_sync_service.py`をインポートするラッパーになりました。
既存のコードは変更なしで動作します。

### 2. integrated_sync_service.py
全ての既存メソッドを提供し、内部で分割されたサービスを呼び出します。

## 使用方法

### 新規コード（推奨）
分割されたサービスを直接使用してください：
```python
from app.services.sync import (
    user_sync_service,
    project_sync_service,
    task_sync_service
)

# ユーザーをインポート
result = await user_sync_service.import_users_from_backlog(
    user=current_user,
    access_token=token,
    db=db
)

# プロジェクトを同期
result = await project_sync_service.sync_all_projects(
    user=current_user,
    access_token=token,
    db=db
)

# タスクを同期
result = await task_sync_service.sync_user_tasks(
    user=current_user,
    access_token=token,
    db=db
)
```

### 既存コード（後方互換性）
既存のコードは変更なしで動作します：
```python
from app.services.sync_service import sync_service

result = await sync_service.sync_user_tasks(user, token, db)
result = await sync_service.sync_all_projects(user, token, db)
result = await sync_service.import_users_from_backlog(user, token, db)
```

## 改善効果

### 1. 可読性の向上
- 元のファイル: 887行 → 各ファイル: 300〜600行
- 各ファイルが特定の責任のみを持つため、理解しやすい

### 2. テスタビリティの向上
- 各サービスを独立してテスト可能
- モックやスタブを使いやすい

### 3. 保守性の向上
- 変更が特定のサービスに限定される
- バグの影響範囲が小さい

### 4. コード重複の削減
- 共通機能は`BaseSyncService`で一元管理
- ユーザー作成、日付パース、エラーハンドリングなどを再利用

### 5. 拡張性の向上
- 新しい同期機能を追加しやすい
- 既存のコードに影響を与えずに拡張可能

## ファイルサイズ比較

| ファイル | 行数 | 責任 |
|---------|------|------|
| 元のsync_service.py | 887行 | 全ての同期機能 |
| base_sync_service.py | 308行 | 共通機能 |
| user_sync_service.py | 539行 | ユーザー同期 |
| project_sync_service.py | 444行 | プロジェクト同期 |
| task_sync_service.py | 619行 | タスク同期 |
| integrated_sync_service.py | 384行 | 後方互換性 |
| __init__.py | 66行 | エクスポート |
| **新sync_service.py（ラッパー）** | **29行** | **インポートのみ** |
| **合計** | **2,360行** | **詳細なコメント込み** |

## 次のステップ

### 1. テストの作成
各サービスのユニットテストを作成してください：
- `tests/services/sync/test_user_sync_service.py`
- `tests/services/sync/test_project_sync_service.py`
- `tests/services/sync/test_task_sync_service.py`

### 2. 統合テストの更新
既存の統合テストが引き続き動作することを確認してください。

### 3. APIエンドポイントの確認
`backend/app/api/v1/sync.py`が新しいサービスで正しく動作することを確認してください。

### 4. ドキュメントの更新
必要に応じて、APIドキュメントや開発者ガイドを更新してください。

## まとめ

このリファクタリングにより、以下を達成しました：

1. **単一責任原則の遵守**: 各サービスが特定の同期機能のみを担当
2. **DRY原則の適用**: 共通機能を基底クラスで実装
3. **後方互換性の維持**: 既存のコードを変更せずに動作
4. **テスタビリティの向上**: 各サービスを独立してテスト可能
5. **保守性の向上**: 変更が特定のサービスに限定される
6. **詳細なコメント**: 全てのファイルに日本語の詳細コメントを追加

新規コードでは、分割されたサービスを直接使用することを推奨します。
既存のコードは変更なしで動作し、段階的に移行できます。
