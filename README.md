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

3. **初回のみフロントエンド依存解決**

   ```bash
   cd frontend
   corepack enable
   yarn install
   cd ..
   ```

4. **サービス起動**

   ```bash
   make start
   ```

5. **アクセス URL**
   - フロントエンド: http://localhost:3000
   - バックエンド API: http://localhost:8000
   - Nginx 経由: http://localhost
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

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

## 🗂️ プロジェクト構成

```
team-insight/
├── frontend/          # React + TypeScript フロントエンド
│   ├── .yarnrc.yml
│   ├── postcss.config.js
│   ├── ...
├── backend/           # FastAPI バックエンド
│   └── app/
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
