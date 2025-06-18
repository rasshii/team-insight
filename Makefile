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
	@echo "  make setup          - 初回セットアップ（Docker環境構築 + DB初期化）"
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
	@echo ""
	@echo "データベース操作:"
	@echo "  make migrate        - DBマイグレーションを実行"
	@echo "  make migrate-down   - マイグレーションを1つ戻す"
	@echo "  make migrate-history - マイグレーション履歴を表示"

# 初回セットアップ
.PHONY: setup
setup:
	@echo "🚀 Team Insight 開発環境をセットアップしています..."
	@echo "📦 必要なディレクトリを確認..."
	@echo "🐳 Dockerイメージをビルド..."
	@$(DOCKER_COMPOSE) build
	@echo "🚀 サービスを起動..."
	@$(DOCKER_COMPOSE) up -d
	@echo "⏳ データベースの起動を待機中..."
	@for i in $$(seq 1 30); do \
		if $(DOCKER_COMPOSE) exec -T $(DB_CONTAINER) pg_isready -U team_insight_user > /dev/null 2>&1; then \
			echo "✅ データベースが起動しました"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 2; \
	done
	@echo ""
	@echo "🗃️  データベースマイグレーションを実行..."
	@$(DOCKER_COMPOSE) exec -T $(BACKEND_CONTAINER) alembic upgrade head
	@echo "✅ マイグレーションが完了しました"
	@echo ""
	@echo "✅ セットアップが完了しました！"
	@echo ""
	@echo "アクセスURL:"
	@echo "  - フロントエンド: http://localhost:3000"
	@echo "  - バックエンドAPI: http://localhost:8000"
	@echo "  - APIドキュメント: http://localhost:8000/docs"
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
	@$(DOCKER_COMPOSE) exec $(DB_CONTAINER) psql -U team_insight_user -d team_insight

# データベースマイグレーション
.PHONY: migrate
migrate:
	@echo "🗄️  データベースマイグレーションを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) alembic upgrade head
	@echo "✅ マイグレーションが完了しました"

# マイグレーションを1つ戻す
.PHONY: migrate-down
migrate-down:
	@echo "⬇️  マイグレーションを1つ戻します..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) alembic downgrade -1
	@echo "✅ ロールバックが完了しました"

# マイグレーション履歴表示
.PHONY: migrate-history
migrate-history:
	@echo "📜 マイグレーション履歴:"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) alembic history

# テスト実行
.PHONY: test
test:
	@echo "🧪 テストを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest
	@echo "✅ テストが完了しました"

# Redisの全キーを表示
.PHONY: redis-keys
redis-keys:
	@echo "🔑 Redisの全キーを表示します..."
	@$(DOCKER_COMPOSE) exec redis redis-cli -a team_insight_redis_password KEYS '*'

# Nginxのアクセスログを表示
.PHONY: nginx-access-log
nginx-access-log:
	@echo "📝 Nginxのアクセスログ（標準出力）を表示します..."
	@$(DOCKER_COMPOSE) logs nginx
