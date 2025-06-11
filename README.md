# Team Insight

チーム分析とコラボレーションのためのプラットフォーム

## 🚀 クイックスタート

### 前提条件

以下のツールがインストールされている必要があります：

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)
- Make（macOS と Linux は標準搭載、Windows は[こちら](http://gnuwin32.sourceforge.net/packages/make.htm)）

### 初回セットアップ

1. **リポジトリをクローン**

   ```bash
   git clone <repository-url>
   cd team-insight
   ```

2. **自動セットアップを実行**

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   または、Makefile を使用：

   ```bash
   make setup
   ```

これで開発環境の構築は完了です！🎉

### アクセス URL

- **フロントエンド**: http://localhost:3000
- **バックエンド API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📖 日常的な使い方

### サービスの起動

```bash
make start
```

### サービスの停止

```bash
make stop
```

### サービスの再起動

```bash
make restart
```

### ログの確認

すべてのサービスのログ：

```bash
make logs
```

特定のサービスのログ：

```bash
make frontend-logs  # フロントエンドのログ
make backend-logs   # バックエンドのログ
make db-logs        # データベースのログ
```

### コンテナへの接続

```bash
make frontend-shell  # フロントエンドコンテナ
make backend-shell   # バックエンドコンテナ
make db-shell        # データベースコンテナ（psqlクライアント）
```

## 🛠️ 開発ガイド

### プロジェクト構成

```
team-insight/
├── frontend/          # React + TypeScript フロントエンド
├── backend/           # FastAPI バックエンド
├── infrastructure/    # Docker設定ファイル
│   └── docker/
│       ├── frontend/
│       ├── backend/
│       ├── postgresql/
│       ├── redis/
│       └── nginx/
├── docker-compose.yml # Docker Compose設定
├── Makefile          # 便利なコマンド集
└── setup.sh          # 初回セットアップスクリプト
```

### データベースマイグレーション

```bash
make migrate
```

### テストの実行

```bash
make test
```

### 環境のクリーンアップ

コンテナとボリュームをすべて削除：

```bash
make clean
```

### イメージの再ビルド

```bash
make rebuild
```

## 🔧 トラブルシューティング

### ポートが既に使用されている場合

他のサービスが同じポートを使用している可能性があります。以下のポートが空いていることを確認してください：

- 3000 (フロントエンド)
- 8000 (バックエンド)
- 5432 (PostgreSQL)
- 6379 (Redis)
- 80 (Nginx)

### Docker の権限エラー

Linux の場合、docker グループにユーザーを追加する必要があります：

```bash
sudo usermod -aG docker $USER
```

その後、ログアウトして再度ログインしてください。

### サービスが起動しない場合

1. Docker が起動していることを確認
2. `docker-compose logs <service-name>` でエラーログを確認
3. `make clean` で環境をクリーンアップしてから再度 `make setup`

## 📝 その他のコマンド

利用可能なすべてのコマンドを確認：

```bash
make help
```

## 🤝 コントリビューション

1. feature ブランチを作成 (`git checkout -b feature/amazing-feature`)
2. 変更をコミット (`git commit -m 'Add some amazing feature'`)
3. ブランチをプッシュ (`git push origin feature/amazing-feature`)
4. プルリクエストを作成

