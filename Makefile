# Team Insight Makefile
# ローカル開発環境の管理用コマンド集

# デフォルトターゲット
.DEFAULT_GOAL := help

# 変数定義
DOCKER_COMPOSE := docker-compose
FRONTEND_CONTAINER := frontend
BACKEND_CONTAINER := backend
DB_CONTAINER := postgres

# ヘルプ
.PHONY: help
help:
	@echo "Team Insight - 開発環境管理コマンド"
	@echo ""
	@echo "使用可能なコマンド:"
	@echo "  make setup          - 初回セットアップ（Docker環境構築）"
	@echo "  make start          - 全サービスを起動"
	@echo "  make stop           - 全サービスを停止"
	@echo "  make restart        - 全サービスを再起動"
	@echo "  make logs           - 全サービスのログを表示"
	@echo "  make status         - サービスの状態を確認"
	@echo "  make clean          - コンテナとボリュームを削除"
	@echo "  make rebuild        - イメージを再ビルド"
	@echo ""
	@echo "個別サービス操作:"
	@echo "  make frontend-logs  - フロントエンドのログを表示"
	@echo "  make backend-logs   - バックエンドのログを表示"
	@echo "  make db-logs        - データベースのログを表示"
	@echo "  make frontend-shell - フロントエンドコンテナに接続"
	@echo "  make backend-shell  - バックエンドコンテナに接続"
	@echo "  make db-shell       - データベースコンテナに接続"

# 初回セットアップ
.PHONY: setup
setup:
	@echo "🚀 Team Insight 開発環境をセットアップしています..."
	@echo "📦 必要なディレクトリを確認..."
	@echo "🐳 Dockerイメージをビルド..."
	@$(DOCKER_COMPOSE) build
	@echo "🚀 サービスを起動..."
	@$(DOCKER_COMPOSE) up -d
	@echo "⏳ サービスの起動を待機中..."
	@sleep 10
	@echo "✅ セットアップが完了しました！"
	@echo ""
	@echo "アクセスURL:"
	@echo "  - フロントエンド: http://localhost:3000"
	@echo "  - バックエンドAPI: http://localhost:8000"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"

# サービス起動
.PHONY: start
start:
	@echo "🚀 サービスを起動しています..."
	@$(DOCKER_COMPOSE) up -d
	@echo "✅ サービスが起動しました"

# サービス停止
.PHONY: stop
stop:
	@echo "🛑 サービスを停止しています..."
	@$(DOCKER_COMPOSE) down
	@echo "✅ サービスが停止しました"

# サービス再起動
.PHONY: restart
restart:
	@echo "🔄 サービスを再起動しています..."
	@$(DOCKER_COMPOSE) restart
	@echo "✅ サービスが再起動しました"

# ログ表示
.PHONY: logs
logs:
	@$(DOCKER_COMPOSE) logs -f

# サービス状態確認
.PHONY: status
status:
	@echo "📊 サービスの状態:"
	@$(DOCKER_COMPOSE) ps

# クリーンアップ
.PHONY: clean
clean:
	@echo "🧹 コンテナとボリュームを削除しています..."
	@$(DOCKER_COMPOSE) down -v
	@echo "✅ クリーンアップが完了しました"

# 再ビルド
.PHONY: rebuild
rebuild:
	@echo "🔨 イメージを再ビルドしています..."
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "✅ 再ビルドが完了しました"

# フロントエンドログ
.PHONY: frontend-logs
frontend-logs:
	@$(DOCKER_COMPOSE) logs -f $(FRONTEND_CONTAINER)

# バックエンドログ
.PHONY: backend-logs
backend-logs:
	@$(DOCKER_COMPOSE) logs -f $(BACKEND_CONTAINER)

# データベースログ
.PHONY: db-logs
db-logs:
	@$(DOCKER_COMPOSE) logs -f $(DB_CONTAINER)

# フロントエンドシェル
.PHONY: frontend-shell
frontend-shell:
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) /bin/sh

# バックエンドシェル
.PHONY: backend-shell
backend-shell:
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) /bin/bash

# データベースシェル
.PHONY: db-shell
db-shell:
	@$(DOCKER_COMPOSE) exec $(DB_CONTAINER) psql -U postgres -d team_insight

# データベースマイグレーション
.PHONY: migrate
migrate:
	@echo "🗄️  データベースマイグレーションを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python -m alembic upgrade head
	@echo "✅ マイグレーションが完了しました"

# テスト実行
.PHONY: test
test:
	@echo "🧪 テストを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest
	@echo "✅ テストが完了しました"
