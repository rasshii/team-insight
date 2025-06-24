# Team Insight Makefile
# ローカル開発環境の管理用コマンド集

# デフォルトターゲット
.DEFAULT_GOAL := help

# 変数定義
DOCKER_COMPOSE := docker-compose
FRONTEND_CONTAINER := frontend
BACKEND_CONTAINER := backend
DB_CONTAINER := postgres
REDIS_CONTAINER := redis

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
	@echo "  make redis-logs     - Redisのログを表示"
	@echo "  make frontend-shell - フロントエンドコンテナに接続"
	@echo "  make backend-shell  - バックエンドコンテナに接続"
	@echo "  make db-shell       - データベースコンテナに接続"
	@echo "  make redis-shell    - Redisコンテナに接続"
	@echo ""
	@echo "データベース操作:"
	@echo "  make migrate        - DBマイグレーションを実行"
	@echo "  make migrate-down   - マイグレーションを1つ戻す"
	@echo "  make migrate-history - マイグレーション履歴を表示"
	@echo ""
	@echo "テスト操作:"
	@echo "  make test           - バックエンドテストを実行"
	@echo "  make test-frontend  - フロントエンドテストを実行"
	@echo "  make test-all       - 全てのテストを実行"
	@echo "  make test-v         - 詳細モードでバックエンドテスト実行"
	@echo "  make test-cov       - カバレッジ付きバックエンドテスト実行"
	@echo "  make test-cov-html  - カバレッジHTMLレポート生成"
	@echo "  make test-failed    - 前回失敗したテストのみ実行"
	@echo "  make test-file FILE=path/to/test.py - 特定ファイルのテスト"
	@echo ""
	@echo "キャッシュ操作:"
	@echo "  make cache-test     - キャッシュ機能をテスト"
	@echo "  make cache-stats    - キャッシュ統計を表示"
	@echo "  make cache-clear    - 全キャッシュをクリア"
	@echo "  make cache-keys     - Redisの全キーを表示"
	@echo ""
	@echo "開発ツール:"
	@echo "  make generate-types - OpenAPIからTypeScript型を生成"
	@echo "  make update-types   - バックエンド起動確認後に型を生成"
	@echo "  make dev-sync       - マイグレーション実行と型生成を一括実行"

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
	@echo "⏳ Redisの起動を待機中..."
	@for i in $$(seq 1 15); do \
		if $(DOCKER_COMPOSE) exec -T $(REDIS_CONTAINER) redis-cli -a team_insight_redis_password ping > /dev/null 2>&1; then \
			echo "✅ Redisが起動しました"; \
			break; \
		fi; \
		echo -n "."; \
		sleep 1; \
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

# Redisログ
.PHONY: redis-logs
redis-logs:
	@$(DOCKER_COMPOSE) logs -f $(REDIS_CONTAINER)

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

# Redisシェル
.PHONY: redis-shell
redis-shell:
	@$(DOCKER_COMPOSE) exec $(REDIS_CONTAINER) redis-cli -a team_insight_redis_password

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

# バックエンドテスト実行
.PHONY: test
test:
	@echo "🧪 バックエンドテストを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest
	@echo "✅ バックエンドテストが完了しました"

# フロントエンドテスト実行
.PHONY: test-frontend
test-frontend:
	@echo "🧪 フロントエンドテストを実行..."
	@$(DOCKER_COMPOSE) exec $(FRONTEND_CONTAINER) yarn test
	@echo "✅ フロントエンドテストが完了しました"

# 全テスト実行
.PHONY: test-all
test-all: test test-frontend
	@echo "✅ 全てのテストが完了しました"

# ==================================================
# 開発ツール
# ==================================================

# TypeScript型の自動生成
.PHONY: generate-types
generate-types:
	@echo "🔄 OpenAPIからTypeScript型を生成..."
	@cd frontend && yarn generate:types
	@echo "✅ 型生成が完了しました"

# APIが変更された後の型更新（バックエンド起動確認付き）
.PHONY: update-types
update-types:
	@echo "🔍 バックエンドの起動を確認..."
	@curl -s http://localhost/api/v1/openapi.json > /dev/null || (echo "❌ バックエンドが起動していません。'make start'を実行してください" && exit 1)
	@$(MAKE) generate-types

# 開発ワークフロー: APIスキーマ変更後の一連の処理
.PHONY: dev-sync
dev-sync: migrate update-types
	@echo "🎉 開発環境の同期が完了しました"
	@echo "  - データベースマイグレーション: ✅"
	@echo "  - TypeScript型生成: ✅"

# 詳細なテスト実行
.PHONY: test-v
test-v:
	@echo "🧪 テストを詳細モードで実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest -v
	@echo "✅ テストが完了しました"

# 特定のファイルのテスト実行
.PHONY: test-file
test-file:
	@echo "🧪 ファイル指定テストを実行..."
	@echo "使用方法: make test-file FILE=tests/test_config.py"
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest $(FILE) -v

# カバレッジ付きテスト実行
.PHONY: test-cov
test-cov:
	@echo "🧪 カバレッジ付きでテストを実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest --cov=app --cov-report=term-missing
	@echo "✅ テストが完了しました"

# カバレッジHTMLレポート生成
.PHONY: test-cov-html
test-cov-html:
	@echo "🧪 カバレッジHTMLレポートを生成..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest --cov=app --cov-report=html
	@echo "✅ HTMLレポートが生成されました: backend/htmlcov/index.html"

# 前回失敗したテストのみ実行
.PHONY: test-failed
test-failed:
	@echo "🧪 前回失敗したテストのみ実行..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest --lf -v

# テスト実行（警告なし）
.PHONY: test-no-warnings
test-no-warnings:
	@echo "🧪 テストを実行（警告非表示）..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) pytest --disable-warnings -v

# キャッシュ機能テスト
.PHONY: cache-test
cache-test:
	@echo "🧪 キャッシュ機能をテストしています..."
	@$(DOCKER_COMPOSE) exec $(BACKEND_CONTAINER) python test_cache.py
	@echo "✅ キャッシュテストが完了しました"

# キャッシュ統計表示
.PHONY: cache-stats
cache-stats:
	@echo "📊 キャッシュ統計を表示します..."
	@$(DOCKER_COMPOSE) exec $(REDIS_CONTAINER) redis-cli -a team_insight_redis_password info stats

# キャッシュクリア
.PHONY: cache-clear
cache-clear:
	@echo "🗑️  全キャッシュをクリアしています..."
	@$(DOCKER_COMPOSE) exec $(REDIS_CONTAINER) redis-cli -a team_insight_redis_password FLUSHDB
	@echo "✅ キャッシュクリアが完了しました"

# Redisの全キーを表示
.PHONY: cache-keys
cache-keys:
	@echo "🔑 Redisの全キーを表示します..."
	@$(DOCKER_COMPOSE) exec $(REDIS_CONTAINER) redis-cli -a team_insight_redis_password KEYS '*'

# Nginxのアクセスログを表示
.PHONY: nginx-access-log
nginx-access-log:
	@echo "📝 Nginxのアクセスログ（標準出力）を表示します..."
	@$(DOCKER_COMPOSE) logs nginx
