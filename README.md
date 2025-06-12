# Team Insight

チーム分析とコラボレーションのためのプラットフォーム

---

## 🚀 初回セットアップ

### 必要なツール

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- Make（macOS/Linux は標準搭載、Windows は[こちら](http://gnuwin32.sourceforge.net/packages/make.htm)）
- Node.js 22.x（yarn v4 は corepack で自動管理されます）

### 手順

1. **リポジトリをクローン**

   ```bash
   git clone <repository-url>
   cd team-insight
   ```

2. **セットアップスクリプトを実行**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   または

   ```bash
   make setup
   ```

   このコマンドで以下が自動的に実行されます：

   - 環境変数ファイル（.env）の作成
   - Docker イメージのビルド
   - 全サービスの起動
   - データベースの起動待機
   - **データベースマイグレーションの実行**（テーブル作成）
   - サービス状態の確認

3. **初回のみフロントエンド依存解決**

   ```bash
   cd frontend
   corepack enable
   yarn install
   cd ..
   ```

4. **アクセス URL**
   - フロントエンド: http://localhost:3000
   - バックエンド API: http://localhost:8000
   - API ドキュメント: http://localhost:8000/docs
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

### セットアップ後の確認

```bash
# サービスの状態確認
make status

# マイグレーションの状態確認
docker-compose exec backend alembic current

# ログの確認（問題がある場合）
make logs
```

---

## 🏃 日常運用コマンド

| 操作                 | コマンド例            | 説明                               |
| -------------------- | --------------------- | ---------------------------------- |
| サービス起動         | `make start`          | 全サービスをバックグラウンド起動   |
| サービス停止         | `make stop`           | 全サービスを停止                   |
| サービス再起動       | `make restart`        | 全サービスを再起動                 |
| サービス状態確認     | `make status`         | サービスの状態一覧を表示           |
| 全ログ表示           | `make logs`           | 全サービスのログをリアルタイム表示 |
| フロントエンドログ   | `make frontend-logs`  | フロントエンドのログのみ表示       |
| バックエンドログ     | `make backend-logs`   | バックエンドのログのみ表示         |
| DB ログ              | `make db-logs`        | データベースのログのみ表示         |
| フロントエンドシェル | `make frontend-shell` | フロントエンドコンテナに入る       |
| バックエンドシェル   | `make backend-shell`  | バックエンドコンテナに入る         |
| DB シェル            | `make db-shell`       | psql で DB に入る                  |
| クリーンアップ       | `make clean`          | コンテナ・ボリュームを全削除       |
| イメージ再ビルド     | `make rebuild`        | Docker イメージを再ビルド          |
| DB マイグレーション  | `make migrate`        | Alembic で DB マイグレーション実行 |
| バックエンドテスト   | `make test`           | バックエンドの pytest を実行       |
| コマンド一覧         | `make help`           | すべてのコマンドを表示             |

---

## 🛠️ 技術スタック

- **フロントエンド**: React + TypeScript, Tailwind CSS v3, shadcn/ui, Yarn v4, Node.js v22
- **バックエンド**: FastAPI, Python 3.11
- **データベース**: PostgreSQL 15
- **キャッシュ**: Redis 7
- **インフラ**: Docker Compose, Nginx

---

## 🗃️ データベースマイグレーション

### Alembic を使用したマイグレーション管理

バックエンドでは Alembic を使用してデータベースのスキーマ管理を行っています。

#### 基本的なマイグレーションコマンド

```bash
# 最新のマイグレーションを適用
make migrate
# または
docker-compose exec backend alembic upgrade head

# 現在のマイグレーション状態を確認
docker-compose exec backend alembic current

# マイグレーション履歴を確認
docker-compose exec backend alembic history
```

#### 新しいマイグレーションファイルの作成

1. **モデルを作成・変更した場合**

   ```bash
   # backend/app/models/ にモデルファイルを作成
   # backend/app/db/base.py にモデルをインポート（重要！）
   ```

2. **自動マイグレーション生成**

   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "説明的なメッセージ"
   ```

3. **手動マイグレーション作成**
   ```bash
   docker-compose exec backend alembic revision -m "説明的なメッセージ"
   ```

#### マイグレーションのロールバック

```bash
# 1つ前のバージョンに戻す
docker-compose exec backend alembic downgrade -1

# 特定のバージョンに戻す
docker-compose exec backend alembic downgrade <revision_id>

# 全てのマイグレーションを取り消す
docker-compose exec backend alembic downgrade base
```

#### 注意事項

- 新しいモデルを作成したら、必ず `backend/app/db/base.py` にインポートを追加してください
- マイグレーションファイルは `backend/migrations/versions/` に保存されます
- 本番環境へのデプロイ前に、必ずマイグレーションファイルをレビューしてください

---

## 🧪 テスト

### バックエンドテスト（pytest）

#### テストの実行

```bash
# 全てのテストを実行
make test
# または
docker-compose exec backend pytest

# 詳細な出力付きでテストを実行
docker-compose exec backend pytest -v

# 特定のテストファイルを実行
docker-compose exec backend pytest tests/test_auth.py

# 特定のテスト関数を実行
docker-compose exec backend pytest tests/test_auth.py::test_get_authorization_url

# カバレッジレポート付きでテストを実行
docker-compose exec backend pytest --cov=app --cov-report=html
```

#### テストファイルの作成

1. **テストファイルの配置**

   ```
   backend/
   ├── app/           # アプリケーションコード
   └── tests/         # テストコード
       ├── conftest.py    # pytest設定とfixture
       ├── test_auth.py   # 認証関連のテスト
       └── test_*.py      # その他のテスト
   ```

2. **基本的なテストの書き方**

   ```python
   # tests/test_example.py
   import pytest
   from fastapi.testclient import TestClient
   from app.main import app

   client = TestClient(app)

   def test_example_endpoint():
       response = client.get("/api/v1/example")
       assert response.status_code == 200
       assert response.json() == {"message": "Hello World"}
   ```

3. **Fixture の使用**

   ```python
   # tests/conftest.py
   import pytest
   from app.db.session import SessionLocal
   from app.models.user import User

   @pytest.fixture(scope="function")
   def test_user():
       """テスト用ユーザーを作成するfixture"""
       db = SessionLocal()
       user = User(
           email="test@example.com",
           hashed_password="dummy_hash",
           full_name="Test User"
       )
       db.add(user)
       db.commit()
       db.refresh(user)

       yield user

       # クリーンアップ
       db.delete(user)
       db.commit()
       db.close()
   ```

4. **非同期関数のモック**

   ```python
   from unittest.mock import AsyncMock, patch

   @patch("app.services.external_api.fetch_data")
   def test_async_function(mock_fetch):
       mock_fetch.return_value = AsyncMock(return_value={"data": "test"})
       # テストコード
   ```

#### テストのベストプラクティス

- テストは独立して実行できるようにする
- Fixture を使用してテストデータを管理する
- 外部 API やサービスはモックを使用する
- テスト後は必ずデータをクリーンアップする
- 意味のあるテスト名を付ける（`test_<機能>_<条件>_<期待結果>`）

---

## 📝 開発フロー

### 新機能開発の流れ

1. **モデルの作成**

   ```bash
   # backend/app/models/new_model.py を作成
   # backend/app/db/base.py にインポートを追加
   ```

2. **マイグレーションの生成と適用**

   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Add new model"
   docker-compose exec backend alembic upgrade head
   ```

3. **API エンドポイントの実装**

   ```bash
   # backend/app/api/v1/new_endpoint.py を作成
   # backend/app/api/v1/__init__.py にルーターを追加
   ```

4. **テストの作成**

   ```bash
   # backend/tests/test_new_endpoint.py を作成
   make test
   ```

5. **フロントエンドの実装**
   ```bash
   # frontend/src/components/NewComponent.tsx を作成
   # frontend/src/services/api.ts にAPIクライアントを追加
   ```

---

## 🗂️ プロジェクト構成

```
team-insight/
├── frontend/          # React + TypeScript フロントエンド
│   ├── .yarnrc.yml
│   ├── postcss.config.js
│   ├── ...
├── backend/           # FastAPI バックエンド
│   ├── app/
│   │   ├── api/       # APIエンドポイント
│   │   ├── core/      # 設定、セキュリティ
│   │   ├── db/        # データベース設定
│   │   ├── models/    # SQLAlchemyモデル
│   │   ├── schemas/   # Pydanticスキーマ
│   │   └── services/  # ビジネスロジック
│   ├── migrations/    # Alembicマイグレーション
│   ├── tests/         # pytestテスト
│   └── alembic.ini    # Alembic設定
├── infrastructure/    # Docker設定ファイル
│   └── docker/
│       ├── frontend/
│       ├── backend/
│       ├── postgresql/
│       ├── redis/
│       └── nginx/
├── docker-compose.yml # Docker Compose設定
├── Makefile           # 便利なコマンド集
└── setup.sh           # 初回セットアップスクリプト
```

---

## 🧩 トラブルシューティング

- **ポート競合**
  3000, 8000, 5432, 6379, 80 が他のプロセスで使われていないか確認

- **Docker 権限エラー（Linux）**

  ```bash
  sudo usermod -aG docker $USER
  # その後ログアウト・再ログイン
  ```

- **サービスが起動しない場合**

  1. Docker が起動しているか確認
  2. `docker-compose logs <service名>` でエラー確認
  3. `make clean` → `make setup` で再構築

- **フロントエンド依存関係の問題**

  ```bash
  cd frontend
  corepack enable
  yarn install
  cd ..
  docker-compose build frontend
  docker-compose restart frontend
  ```

- **バックエンドで pydantic の extra_forbidden エラー**

  - `app/core/config.py` の `Settings` クラスに `REDIS_URL: str = "redis://redis:6379"` を追加

- **マイグレーションエラー**

  - `alembic.ini` の `sqlalchemy.url` が正しく設定されているか確認
  - モデルが `backend/app/db/base.py` にインポートされているか確認
  - データベースが起動しているか確認: `docker-compose ps postgres`

- **テストエラー**
  - テスト用データベースが正しく設定されているか確認
  - Fixture が正しく `conftest.py` に定義されているか確認
  - モックが適切に設定されているか確認（同期/非同期の違いに注意）

---

## 🤝 コントリビューション

1. feature ブランチを作成
   `git checkout -b feature/your-feature`
2. 変更をコミット
   `git commit -m 'Add your feature'`
3. ブランチをプッシュ
   `git push origin feature/your-feature`
4. プルリクエストを作成

---

## 💡 補足

- `.gitignore`はプロジェクトルートと frontend 配下の両方に設置し、用途ごとに管理しています。
- Node.js 22 + Yarn v4(Corepack) + Tailwind CSS v3 + Docker Compose の組み合わせで安定動作を確認済みです。
- 詳細なコマンドや運用フローは`Makefile`や本 README を参照してください。
