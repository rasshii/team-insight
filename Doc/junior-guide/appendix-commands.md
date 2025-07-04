# コマンドリファレンス

このドキュメントは、Team Insight開発で使用する主要なコマンドをまとめたリファレンスです。各コマンドの意味、使い方、実行結果を詳しく解説します。

## 🌟 はじめに：コマンドとは？

### 💻 コマンドラインインターフェース（CLI）

**コマンド = コンピュータへの文字による命令**

```
GUI（グラフィカル）         CLI（コマンドライン）
┌─────────────┐          ┌─────────────┐
│ マウスで     │          │ $ make start │
│ ボタンを     │    vs    │ （文字で     │
│ クリック     │          │  命令）      │
└─────────────┘          └─────────────┘

メリット：
- 高速な操作
- 自動化が可能
- 複雑な操作も1行で実行
```

### 🎯 なぜMakefileを使うのか？

**Makefile = よく使うコマンドをまとめた便利帳**

```bash
# Makefileがない場合
docker-compose -f docker-compose.yml up -d postgres redis
docker-compose -f docker-compose.yml up -d backend
docker-compose -f docker-compose.yml up -d frontend nginx
# ...長くて覚えられない！

# Makefileがある場合
make start
# 簡単！
```

## 📋 Makefileコマンド一覧

### 基本操作

#### 🚀 初回セットアップ

```bash
make setup
```

**何をするか**：開発環境を最初から構築
- Dockerイメージをビルド
- データベースを作成
- 初期マイグレーションを実行
- 初期データを投入

**いつ使うか**：
- プロジェクトをクローンした直後
- 環境を完全にリセットしたい時

**実行結果**：
```
Creating network "team-insight_default"...
Building backend...
Building frontend...
Creating postgres... done
Creating redis... done
Running migrations...
Setup complete! Access http://localhost
```

#### 🎮 サービス起動・停止

```bash
make start          # 全サービス起動
```
**何をするか**：すべてのDockerコンテナを起動
- PostgreSQL、Redis（データストア）
- Backend、Frontend（アプリケーション）
- Nginx（リバースプロキシ）

**いつ使うか**：開発作業を始める時

```bash
make stop           # 全サービス停止
```
**何をするか**：すべてのコンテナを停止（データは保持）

**いつ使うか**：開発作業を終える時

```bash
make restart        # 全サービス再起動
```
**何をするか**：stop → start を順番に実行

**いつ使うか**：設定変更を反映させたい時

```bash
make status         # サービス状態確認
```
**実行結果の例**：
```
NAME                 STATUS    PORTS
team-insight-postgres   Up      5432/tcp
team-insight-redis      Up      6379/tcp
team-insight-backend    Up      8000/tcp
team-insight-frontend   Up      3000/tcp
team-insight-nginx      Up      0.0.0.0:80->80/tcp
```

#### 🧹 クリーンアップ

```bash
make clean          # コンテナとボリューム削除
```
**何をするか**：
- すべてのコンテナを削除
- データベースのデータも削除（⚠️ 注意）
- ネットワーク設定も削除

**いつ使うか**：
- 完全に環境をリセットしたい時
- ディスク容量を空けたい時

```bash
make rebuild        # キャッシュなしで再ビルド
```
**何をするか**：
- Dockerのビルドキャッシュを使わずに再構築
- 最新の依存関係をインストール

**いつ使うか**：
- requirements.txtやpackage.jsonを更新した時
- ビルドエラーが解決しない時

### ログ確認

#### 📝 ログとは？

**ログ = アプリケーションの動作記録**

```
ログの例：
[2024-01-15 10:30:45] INFO: User logged in: tanaka@example.com
[2024-01-15 10:31:02] ERROR: Database connection failed
[2024-01-15 10:31:03] DEBUG: Retrying connection...
```

#### 🔍 全サービスのログ

```bash
make logs           # リアルタイムログ（Ctrl+Cで終了）
```
**何を見られるか**：すべてのサービスのログを同時に表示
**使い方**：
- 新しいログが自動的に表示される
- Ctrl+C で表示を終了

```bash
make logs-tail      # 最新100行
```
**何を見られるか**：各サービスの最新100行のログ
**いつ使うか**：エラーを確認したい時

#### 🎯 サービス別ログ

```bash
make frontend-logs  # フロントエンドログ
```
**よく見るログ**：
```
✓ Compiled successfully
▲ Next.js 14.1.0
- Local: http://localhost:3000
```

```bash
make backend-logs   # バックエンドログ
```
**よく見るログ**：
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
make db-logs        # データベースログ
```
**何を確認できるか**：
- データベース接続
- 実行されたSQL
- エラー情報

#### 🚦 Nginxアクセスログ

```bash
make nginx-access-log   # アクセスログ
```
**ログの見方**：
```
192.168.1.1 - - [15/Jan/2024:10:30:45 +0000] "GET /api/v1/users HTTP/1.1" 200 1234
└─ IPアドレス   └─ 日時                      └─ リクエスト            └─ ステータス └─ サイズ
```

```bash
make nginx-error-log    # エラーログ
```
**何が分かるか**：
- 404エラー（ページが見つからない）
- 502エラー（バックエンドが停止中）
- 設定ミス

### シェルアクセス

#### 🐚 シェルとは？

**シェル = コンテナ内部のコマンドライン**

```
ホストマシン              コンテナ内部
┌─────────────┐         ┌─────────────┐
│ $ make       │   →→→   │ root@abc123:│
│ backend-shell│         │ /app#       │
└─────────────┘         └─────────────┘
```

#### 💻 各コンテナへのアクセス

```bash
make frontend-shell # フロントエンドコンテナ
```
**中で何ができるか**：
```bash
# パッケージの確認
yarn list
# ファイルの確認
ls -la src/
# 環境変数の確認
env | grep NEXT_
```

```bash
make backend-shell  # バックエンドコンテナ
```
**中で何ができるか**：
```bash
# Pythonインタープリタ起動
python
>>> from app.models import User
>>> # データベース操作が可能

# インストール済みパッケージ
pip list

# マイグレーション状態確認
alembic current
```

```bash
make db-shell       # PostgreSQLコンテナ
```
**自動的にpsqlに接続**：
```sql
teaminsight=# \dt team_insight.*  -- テーブル一覧
teaminsight=# SELECT COUNT(*) FROM team_insight.users;
```

**終了方法**：`\q` または `Ctrl+D`

### データベース管理

#### 🗄️ マイグレーション管理

**マイグレーション = データベース構造の変更管理**

```bash
make migrate         # 最新版まで適用
```
**何をするか**：
- 未適用のマイグレーションをすべて実行
- テーブルの作成・変更・削除を自動実行

**実行結果の例**：
```
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add phone_number to users
INFO  [alembic.runtime.migration] Running upgrade def456 -> ghi789, create teams table
```

```bash
make migrate-down    # 1つ前に戻す
```
**何をするか**：直前のマイグレーションを取り消し
**いつ使うか**：マイグレーションでエラーが起きた時

```bash
make migrate-history # マイグレーション履歴
```
**実行結果の例**：
```
abc123 -> def456 (head), add phone_number to users
        -> abc123, create teams table
<base> -> xyz999, initial schema
```

```bash
make migrate-create MSG="add_new_column"  # 新規作成
```
**何をするか**：新しいマイグレーションファイルを生成
**作成されるファイル**：
```
migrations/versions/hij567_add_new_column.py
```

#### 💾 バックアップ・リストア

```bash
make db-backup      # バックアップ作成
```
**何をするか**：
- データベース全体をSQLファイルに保存
- backups/ディレクトリに日時付きで保存

**保存先の例**：
```
backups/teaminsight_20240115_103045.sql
```

```bash
make db-restore     # 最新のバックアップから復元
```
**何をするか**：
- 最新のバックアップファイルを探す
- データベースを完全に復元
- ⚠️ 現在のデータは失われます

```bash
make db-list-backups # バックアップ一覧
```
**実行結果の例**：
```
teaminsight_20240115_103045.sql (156MB)
teaminsight_20240114_020000.sql (154MB)
teaminsight_20240113_020000.sql (152MB)
```

#### ⚠️ 危険な操作

```bash
make db-reset       # データベースリセット（危険）
```
**何をするか**：
1. すべてのテーブルを削除
2. マイグレーションを最初から実行
3. 初期データを投入

**⚠️ 注意**：すべてのデータが失われます！

```bash
make db-seed        # テストデータ投入
```
**何をするか**：開発用のダミーデータを追加
- テストユーザー
- サンプルプロジェクト
- ダミータスク

### ユーザー・ロール管理

#### 👥 ロールとは？

**ロール = ユーザーの役割（権限の集まり）**

```
Team Insightのロール：
┌─────────────────┐
│     ADMIN       │ → すべての操作が可能
├─────────────────┤
│ PROJECT_LEADER  │ → プロジェクト管理権限
├─────────────────┤
│    MEMBER       │ → 基本的な閲覧・操作権限
└─────────────────┘
```

#### 🔐 管理者設定

```bash
make init-admin     # 環境変数から初期管理者設定
```
**前提条件**：`.env`ファイルに設定が必要
```
INITIAL_ADMIN_EMAILS=admin@example.com,manager@example.com
```

```bash
make set-admin EMAIL=user@example.com  # 特定ユーザーを管理者に
```
**何をするか**：
- 指定したユーザーにADMINロールを付与
- すべての機能にアクセス可能になる

**実行結果**：
```
Setting admin role for user@example.com...
✓ User user@example.com is now an admin
```

#### 🎭 ロール管理

```bash
make set-role EMAIL=user@example.com ROLE=PROJECT_LEADER
```
**使用可能なロール**：
- `ADMIN`：システム管理者
- `PROJECT_LEADER`：プロジェクトリーダー
- `MEMBER`：一般メンバー

```bash
make remove-role EMAIL=user@example.com ROLE=MEMBER
```
**何をするか**：指定したロールを削除
**注意**：すべてのロールを削除するとアクセス不可に

```bash
make list-users     # 全ユーザーとロール一覧
```
**実行結果の例**：
```
Email                    Name           Roles                    Active
────────────────────────────────────────────────────────────────────────
admin@example.com       管理者太郎      ADMIN                    ✓
tanaka@example.com      田中花子        PROJECT_LEADER, MEMBER   ✓
sato@example.com        佐藤次郎        MEMBER                   ✓
inactive@example.com    退職者          MEMBER                   ✗
```

### テスト実行

```bash
# バックエンドテスト
make test           # 全テスト実行
make test-verbose   # 詳細出力
make test-coverage  # カバレッジレポート付き
make test-unit      # ユニットテストのみ
make test-integration # 統合テストのみ

# 型チェック・静的解析
make type-check     # mypyによる型チェック
make lint           # flake8によるリント
make format         # blackによる自動フォーマット
```

### 開発支援

```bash
# API関連
make api-docs       # APIドキュメントを開く
make generate-types # OpenAPIからTypeScript型生成

# キャッシュ管理
make redis-keys     # Redisのキー一覧
make redis-flush    # Redisキャッシュクリア

# 開発サーバー（ホットリロード付き）
make dev            # 開発モードで起動
make dev-backend    # バックエンドのみ開発モード
make dev-frontend   # フロントエンドのみ開発モード
```

## 🐳 Docker Composeコマンド

### 📦 Docker Composeとは？

**Docker Compose = 複数のコンテナをまとめて管理するツール**

```
docker-compose.yml に定義：
┌─────────────┐
│  postgres   │ ←─┐
├─────────────┤   │
│   redis     │ ←─┤ 一括管理
├─────────────┤   │
│  backend    │ ←─┤
├─────────────┤   │
│  frontend   │ ←─┤
├─────────────┤   │
│   nginx     │ ←─┘
└─────────────┘
```

### 基本操作

```bash
docker-compose up -d        # バックグラウンドで起動
```
**オプションの意味**：
- `up`：コンテナを作成して起動
- `-d`（detached）：バックグラウンドで実行

```bash
docker-compose down         # 停止と削除
```
**何が起こるか**：
1. コンテナを停止
2. コンテナを削除
3. ネットワークを削除
4. **データは保持**（ボリューム）

```bash
docker-compose ps           # 状態確認
```
**表示される情報**：
```
NAME                    COMMAND                  SERVICE    STATUS    PORTS
team-insight-postgres   "docker-entrypoint..."   postgres   Up        5432/tcp
team-insight-backend    "uvicorn app.main..."    backend    Up        8000/tcp
```

#### 🎯 特定サービスのみ操作

```bash
docker-compose up -d backend    # バックエンドのみ起動
```
**いつ使うか**：
- バックエンドのコードを変更した後
- バックエンドだけ再起動したい時

```bash
docker-compose stop frontend    # フロントエンドのみ停止
```
**stopとdownの違い**：
- `stop`：コンテナを停止（削除しない）
- `down`：コンテナを停止して削除

### ビルド操作

#### 🏗️ ビルドとは？

**ビルド = Dockerイメージの作成（アプリケーションの実行環境を構築）**

```
Dockerfile → ビルド → Dockerイメージ → 実行 → コンテナ
└─ 設計図    └─ 構築    └─ 実行可能な環境  └─ 動作  └─ 実行中のアプリ
```

#### 全サービスのビルド
```bash
docker-compose build
```

**何をするか**：
1. docker-compose.ymlに定義された全サービスをビルド
2. Dockerfileの指示に従って環境構築
3. 依存パッケージのインストール
4. アプリケーションコードのコピー

**実行結果の例**：
```
Building postgres...
[+] Building 0.5s (3/3) FINISHED
Building backend...
[+] Building 45.2s (15/15) FINISHED
 => [1/10] FROM python:3.11-slim
 => [2/10] RUN apt-get update && apt-get install -y...
 => [3/10] WORKDIR /app
 => [4/10] COPY requirements.txt .
 => [5/10] RUN pip install -r requirements.txt
```

#### キャッシュなしでビルド
```bash
docker-compose build --no-cache
```

**なぜキャッシュを無効にするか**：
- 通常のビルドでは前回の結果を再利用（高速化）
- しかし、以下の場合はキャッシュが問題になる：
  - 外部パッケージの最新版を取得したい
  - ビルドエラーの原因がキャッシュにある
  - Dockerfileの変更が反映されない

**使用例**：
```bash
# requirements.txtを更新したが反映されない時
docker-compose build --no-cache backend
```

#### 特定サービスのみビルド
```bash
docker-compose build backend     # バックエンドのみ
docker-compose build frontend    # フロントエンドのみ
```

**メリット**：
- 変更したサービスだけビルド（時間短縮）
- 他のサービスに影響を与えない

#### イメージの取得（pull）
```bash
docker-compose pull
```

**何をするか**：
- Docker Hubから最新のベースイメージを取得
- postgres:15、redis:7.0.15などの公式イメージ

**いつ使うか**：
- ベースイメージのセキュリティアップデートを適用したい時
- 新しい環境でプロジェクトをセットアップする時

#### イメージのプッシュ（push）
```bash
docker-compose push
```

**何をするか**：
- ビルドしたイメージをDockerレジストリに送信
- 他の開発者やサーバーで同じイメージを使用可能に

**注意**：通常は CI/CD パイプラインで自動実行される

### ログとデバッグ

#### 📋 Docker Composeでのログ確認

##### リアルタイムログ追跡
```bash
docker-compose logs -f
```

**オプションの意味**：
- `-f` (follow)：新しいログを継続的に表示
- リアルタイムで問題を追跡できる
- `Ctrl+C` で終了

**表示例**：
```
backend_1   | INFO:     Started server process [1]
frontend_1  | ✓ Compiled successfully
postgres_1  | 2024-01-15 10:30:45.123 JST [1] LOG: database system is ready
redis_1     | 1:M 15 Jan 2024 10:30:45.100 * Ready to accept connections
```

##### 特定サービスのログ
```bash
docker-compose logs -f backend  # バックエンドのみ
docker-compose logs -f frontend postgres  # 複数指定も可能
```

**使い分け**：
- エラーの原因を特定したい時
- 特定のサービスの動作を確認したい時

##### ログの絞り込み
```bash
docker-compose logs --tail=100  # 最新100行のみ
docker-compose logs --tail=50 backend  # バックエンドの最新50行
```

**なぜ使うか**：
- 全ログは膨大で読みづらい
- エラーは通常最後の方に出力される

##### タイムスタンプ付きログ
```bash
docker-compose logs -t
```

**表示例**：
```
2024-01-15T10:30:45.123456789Z backend_1 | INFO: Request received
2024-01-15T10:30:45.234567890Z backend_1 | ERROR: Database connection failed
```

**メリット**：
- エラーの発生時刻が正確にわかる
- 複数サービス間のタイミング問題を調査できる

#### 🐛 デバッグ操作

##### コンテナ内でコマンド実行
```bash
docker-compose exec backend bash
```

**execとは**：
- 実行中のコンテナ内でコマンドを実行
- デバッグやファイル確認に使用

**コンテナ内でできること**：
```bash
# Pythonインタープリタ起動
python
>>> from app.models import User
>>> User.query.all()

# ファイル確認
ls -la /app/
cat /app/.env

# プロセス確認
ps aux
```

##### 新しいコンテナでコマンド実行
```bash
docker-compose run --rm backend env
```

**runとexecの違い**：
- `exec`：既存のコンテナ内で実行
- `run`：新しいコンテナを作成して実行
- `--rm`：実行後にコンテナを自動削除

**使用例**：
```bash
# 環境変数の確認
docker-compose run --rm backend env | grep DATABASE

# Pythonスクリプトの実行
docker-compose run --rm backend python scripts/test_connection.py

# マイグレーションの実行
docker-compose run --rm backend alembic upgrade head
```

##### プロセス一覧
```bash
docker-compose top
```

**表示例**：
```
team-insight-backend
UID    PID    PPID   C   STIME   TTY   TIME       CMD
root   1234   1000   0   10:30   ?     00:00:15   python -m uvicorn app.main:app
root   1235   1234   0   10:30   ?     00:00:05   /usr/local/bin/python
```

**確認できること**：
- メモリリークしているプロセス
- CPU使用率が高いプロセス
- 予期しないプロセスの存在

## 🐍 Pythonコマンド（バックエンド）

### パッケージ管理

#### 📦 pipとは？

**pip = Python Package Installer（Pythonのパッケージ管理ツール）**

```
npm (JavaScript) ≈ pip (Python) ≈ gem (Ruby)
```

#### 依存関係のインストール
```bash
pip install -r requirements.txt
```

**何をするか**：
- requirements.txtに記載されたパッケージを一括インストール
- バージョンも指定通りにインストール

**requirements.txtの中身の例**：
```
fastapi==0.109.2
pydantic==2.6.1
sqlalchemy==2.0.27
redis==5.0.1
```

#### 開発用パッケージのインストール
```bash
pip install -r requirements-dev.txt
```

**開発用パッケージとは**：
- テストツール（pytest、pytest-cov）
- コード品質ツール（black、flake8、mypy）
- デバッグツール（ipython、ipdb）

#### 新しいパッケージの追加
```bash
# 1. パッケージをインストール
pip install requests

# 2. requirements.txtに追加
pip freeze > requirements.txt
```

**⚠️ 注意**：
- `pip freeze`は仮想環境内で実行すること
- グローバル環境で実行すると不要なパッケージも含まれる

**より安全な方法**：
```bash
# 特定のパッケージだけ追加
echo "requests==2.31.0" >> requirements.txt
```

### FastAPI開発

#### 🚀 開発サーバーの起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**オプションの意味**：
- `app.main:app`：app/main.pyファイルのappオブジェクトを起動
- `--reload`：コード変更時に自動再起動（開発時のみ）
- `--host 0.0.0.0`：すべてのネットワークインターフェースで受信
- `--port 8000`：ポート8000で起動

**起動時のログ**：
```
INFO:     Will watch for changes in these directories: ['/app']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [1] using StatReload
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 本番サーバーの起動
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**オプションの意味**：
- `-w 4`：4つのワーカープロセスを起動（CPUコア数に合わせる）
- `-k uvicorn.workers.UvicornWorker`：非同期処理対応のワーカー

**開発用uvicornとの違い**：
- 複数のワーカーで並列処理（高負荷対応）
- 自動再起動なし（安定性重視）
- プロセス管理機能あり

#### OpenAPI仕様のエクスポート
```bash
python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json
```

**何をするか**：
- FastAPIが自動生成するAPI仕様をJSON形式で出力
- フロントエンドの型生成に使用
- API ドキュメントの元データ

**もっと簡単な方法**：
```bash
# APIドキュメントにアクセス
curl http://localhost:8000/openapi.json > openapi.json
```

### データベース操作

#### 🗄️ Alembicマイグレーション

##### 新しいマイグレーションの作成
```bash
alembic revision --autogenerate -m "add phone_number to users"
```

**何が起こるか**：
1. モデルの変更を自動検出
2. マイグレーションファイルを生成
3. `migrations/versions/`に保存

**生成されるファイルの例**：
```python
"""add phone_number to users

Revision ID: abc123
Revises: def456
Create Date: 2024-01-15 10:30:45.123456

"""
def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(20)))

def downgrade():
    op.drop_column('users', 'phone_number')
```

##### マイグレーションの実行
```bash
alembic upgrade head  # 最新版まで適用
alembic upgrade +1    # 1つだけ進める
alembic upgrade abc123  # 特定のリビジョンまで
```

##### マイグレーションの取り消し
```bash
alembic downgrade -1    # 1つ前に戻す
alembic downgrade base  # 初期状態に戻す（危険！）
```

**いつ使うか**：
- マイグレーションでエラーが発生した時
- 開発中に変更を取り消したい時

#### SQLAlchemy シェル
```bash
python -c "from app.db.session import SessionLocal; db = SessionLocal(); from IPython import embed; embed()"
```

**対話的にデータベース操作**：
```python
# ユーザーを検索
from app.models import User
users = db.query(User).all()
for user in users:
    print(f"{user.name}: {user.email}")

# 新しいユーザーを作成
new_user = User(name="新規ユーザー", email="new@example.com")
db.add(new_user)
db.commit()

# 条件検索
active_users = db.query(User).filter(User.is_active == True).count()
print(f"アクティブユーザー数: {active_users}")
```

**終了方法**：`exit()` または `Ctrl+D`

## 📦 Node.js/Yarnコマンド（フロントエンド）

### パッケージ管理

#### 🧶 Yarnとは？

**Yarn = JavaScriptのパッケージマネージャー（npmの高速版）**

```
Team InsightではYarn Berry (v4)を使用
├─ 高速インストール
├─ 厳密な依存関係管理
└─ ゼロインストール対応
```

#### 依存関係のインストール
```bash
yarn install
```

**何をするか**：
- package.jsonに記載されたパッケージをインストール
- yarn.lockファイルで厳密なバージョン管理
- .pnp.cjsファイルにパッケージ情報を記録

**実行結果の例**：
```
➤ YN0000: ┌ Resolution step
➤ YN0000: │ ✓ react@npm:18.2.0
➤ YN0000: │ ✓ next@npm:14.1.0
➤ YN0000: └ Completed in 2s 341ms
➤ YN0000: ┌ Fetch step
➤ YN0000: └ Completed in 5s 123ms
➤ YN0000: ┌ Link step
➤ YN0000: └ Completed in 1s 456ms
➤ YN0000: Done in 8s 920ms
```

#### パッケージの追加
```bash
yarn add package-name          # 本番依存関係
yarn add -D package-name       # 開発依存関係
```

**例**：
```bash
# チャートライブラリを追加
yarn add recharts

# 型定義を開発依存関係として追加
yarn add -D @types/recharts
```

**package.jsonへの反映**：
```json
{
  "dependencies": {
    "recharts": "^2.10.3"
  },
  "devDependencies": {
    "@types/recharts": "^1.8.28"
  }
}
```

#### パッケージの削除
```bash
yarn remove package-name
```

**何が起こるか**：
1. package.jsonから削除
2. yarn.lockを更新
3. 不要なファイルをクリーンアップ

#### インタラクティブアップグレード
```bash
yarn upgrade-interactive
```

**表示例**：
```
? Choose which packages to update. (Press <space> to select)
❯ ◯ next                  14.0.0 → 14.1.0
  ◯ @types/react         18.2.0 → 18.2.45
  ◯ eslint                8.50.0 → 8.56.0
```

**操作方法**：
- スペースキーで選択/解除
- Enterで実行
- メジャーバージョンアップには注意

### Next.js開発

#### ⚡ 開発サーバーの起動
```bash
yarn dev
```

**何をするか**：
- Next.js開発サーバーを起動
- ホットリロード機能（自動更新）
- エラーのリアルタイム表示

**起動時のログ**：
```
▲ Next.js 14.1.0
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 2.5s
```

**ホットリロードとは**：
```
コード変更 → 自動検知 → ブラウザ自動更新
                ↓
            手動リロード不要！
```

#### プロダクションビルド
```bash
yarn build
```

**何をするか**：
1. TypeScriptのコンパイル
2. コードの最適化（圧縮・バンドル）
3. 静的ページの生成
4. ビルドサイズの分析

**ビルド結果の例**：
```
Route (app)                              Size     First Load JS
┌ ○ /                                    178 B          87.2 kB
├ ○ /api/health                          0 B                0 B
├ ○ /dashboard/personal                  3.42 kB        95.6 kB
└ ○ /projects                            2.18 kB        89.4 kB

○  (Static)  prerendered as static content
```

**記号の意味**：
- `○` 静的ページ（事前生成）
- `λ` サーバーサイドレンダリング
- `◐` インクリメンタル静的再生成

#### プロダクションサーバーの起動
```bash
yarn start
```

**前提条件**：`yarn build`の実行が必要

**開発サーバーとの違い**：
| 項目 | yarn dev | yarn start |
|------|----------|------------|
| 用途 | 開発時 | 本番環境 |
| 速度 | 遅い | 高速 |
| 最適化 | なし | あり |
| エラー表示 | 詳細 | 最小限 |

#### バンドルサイズ分析
```bash
yarn analyze
```

**何がわかるか**：
- どのライブラリが容量を占めているか
- 不要なコードが含まれていないか
- 最適化の余地があるか

**分析結果の見方**：
```
Bundle Analysis
├─ node_modules (850KB)
│  ├─ react-dom (120KB)
│  ├─ @tanstack/react-query (95KB)
│  └─ d3 (280KB) ← 大きい！
└─ src (150KB)
```

#### TypeScriptチェック
```bash
yarn type-check
```

**何をするか**：
- 型エラーのチェック
- ビルド前の事前確認
- CIでの自動チェック

**エラー例**：
```typescript
src/components/UserCard.tsx:15:5
Type 'string' is not assignable to type 'number'.
  13 |   const user: User = {
  14 |     id: 1,
> 15 |     age: "25", // ← エラー：数値型に文字列
  16 |   }
```

### テストとリント

#### 🧪 テストの実行

##### 基本的なテスト実行
```bash
yarn test
```

**何をテストするか**：
- コンポーネントの動作
- 関数の正しい結果
- エラーハンドリング

**テスト結果の例**：
```
 PASS  src/components/UserCard.test.tsx
  UserCard
    ✓ renders user name correctly (35 ms)
    ✓ shows active badge when user is active (12 ms)
    ✓ handles missing data gracefully (8 ms)

Test Suites: 1 passed, 1 total
Tests:       3 passed, 3 total
```

##### ウォッチモード
```bash
yarn test:watch
```

**何が便利か**：
- ファイル変更を監視
- 変更されたテストのみ自動実行
- 開発中のTDD（テスト駆動開発）に最適

**操作方法**：
```
Watch Usage
 › Press f to run only failed tests
 › Press o to only run tests related to changed files
 › Press p to filter by a filename regex pattern
 › Press q to quit watch mode
```

##### カバレッジレポート
```bash
yarn test:coverage
```

**カバレッジとは**：テストがコードの何％をカバーしているか

**レポートの見方**：
```
--------------------|---------|----------|---------|---------|
File                | % Stmts | % Branch | % Funcs | % Lines |
--------------------|---------|----------|---------|---------|
All files           |   85.71 |       75 |     100 |   85.71 |
 components/        |   90.00 |       80 |     100 |   90.00 |
  UserCard.tsx      |   95.00 |       90 |     100 |   95.00 |
  ProjectList.tsx   |   85.00 |       70 |     100 |   85.00 |
--------------------|---------|----------|---------|---------|
```

**目標**：80%以上のカバレッジを維持

#### 🔍 リント（コード品質チェック）

##### ESLintの実行
```bash
yarn lint
```

**何をチェックするか**：
- コーディングルール違反
- 潜在的なバグ
- パフォーマンス問題
- アクセシビリティ

**エラー例**：
```
src/pages/index.tsx
  12:5  error  'useState' is defined but never used     @typescript-eslint/no-unused-vars
  25:3  warning  Missing dependency 'userId' in useEffect  react-hooks/exhaustive-deps
```

##### 自動修正
```bash
yarn lint:fix
```

**自動修正できるもの**：
- インデント
- セミコロンの有無
- クォートの統一
- 未使用のimport削除

**自動修正できないもの**：
- ロジックエラー
- 型エラー
- 複雑なルール違反

##### Prettierでフォーマット
```bash
yarn format
```

**Prettierとは**：コードフォーマッター（整形ツール）

**整形内容**：
```javascript
// 整形前
const user={name:"田中",age:25,isActive:true}

// 整形後
const user = {
  name: "田中",
  age: 25,
  isActive: true,
};
```

**VSCodeとの連携**：
```json
// .vscode/settings.json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode"
}
```

## 🗃️ PostgreSQLコマンド

### 基本操作

#### 🐘 PostgreSQLとは？

**PostgreSQL = 高機能なオープンソースデータベース**

```
Team Insightでの使用:
├─ ユーザー情報の保存
├─ プロジェクト・タスクデータ
├─ 権限管理（RBAC）
└─ レポート配信履歴
```

#### psqlコマンドライン

##### データベース接続
```sql
\c teaminsight
```

**何をするか**：teaminsightデータベースに接続

**実行結果**：
```
You are now connected to database "teaminsight" as user "teaminsight".
```

##### テーブル一覧の表示
```sql
\dt team_insight.*
```

**表示例**：
```
                    List of relations
    Schema    |         Name          | Type  |   Owner    
--------------+-----------------------+-------+------------
 team_insight | activity_logs         | table | teaminsight
 team_insight | login_history         | table | teaminsight
 team_insight | projects              | table | teaminsight
 team_insight | tasks                 | table | teaminsight
 team_insight | teams                 | table | teaminsight
 team_insight | users                 | table | teaminsight
```

**スキーマとは**：
```
データベース
└─ スキーマ（名前空間）
   └─ テーブル

例：team_insight.users
    └─ スキーマ名.テーブル名
```

##### テーブル構造の確認
```sql
\d+ team_insight.users
```

**表示内容**：
```
                                 Table "team_insight.users"
    Column    |            Type             | Modifiers | Storage  | Description
--------------+-----------------------------+-----------+----------+-------------
 id           | integer                     | not null  | plain    | 
 email        | character varying(255)      | not null  | extended | 
 name         | character varying(100)      |           | extended | 
 is_active    | boolean                     | default t | plain    | 
 created_at   | timestamp without time zone |           | plain    | 
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "users_email_key" UNIQUE CONSTRAINT, btree (email)
```

#### データ操作

##### データの確認
```sql
-- 最初の10件を表示
SELECT * FROM team_insight.users LIMIT 10;
```

**LIMITを使う理由**：
- 大量データの場合、全件表示は時間がかかる
- 画面に収まらない
- データベースへの負荷軽減

##### 件数の確認
```sql
SELECT COUNT(*) FROM team_insight.tasks;
```

**結果例**：
```
 count 
-------
  1523
(1 row)
```

##### 条件付き検索
```sql
-- アクティブユーザーのみ
SELECT name, email 
FROM team_insight.users 
WHERE is_active = true
ORDER BY created_at DESC
LIMIT 20;
```

**SQLキーワードの意味**：
- `WHERE`：条件指定
- `ORDER BY`：並び替え
- `DESC`：降順（新しい順）
- `ASC`：昇順（古い順）

### メンテナンス

#### 🧹 VACUUMとは？

**VACUUM = データベースの掃除機能**

```sql
VACUUM ANALYZE team_insight.tasks;
```

**なぜ必要か**：
- PostgreSQLは削除したデータを即座に消さない
- 「削除マーク」をつけるだけ（高速化のため）
- VACUUMで実際に削除して領域を回収

**ANALYZEの効果**：
- テーブルの統計情報を更新
- クエリの実行計画を最適化
- 検索速度の向上

**実行タイミング**：
- 通常は自動実行（autovacuum）
- 大量削除・更新後は手動実行推奨

#### 🔧 インデックスの再構築

```sql
REINDEX TABLE team_insight.tasks;
```

**インデックスとは**：
```
本の索引のようなもの
├─ データを高速検索
├─ しかし時間とともに断片化
└─ 再構築で性能回復
```

**いつ使うか**：
- 検索が遅くなった時
- 大量のデータ更新後
- ディスク容量を節約したい時

#### 📊 統計情報の更新

```sql
ANALYZE team_insight.projects;
```

**統計情報とは**：
- データの分布状況
- カラムの値の種類
- NULLの割合

**PostgreSQLの動作**：
```
SQLクエリ → 統計情報を参照 → 最適な実行計画 → 高速実行
             ↑
          ANALYZEで更新
```

#### メンテナンスコマンドの使い分け

| コマンド | 用途 | 実行頻度 |
|---------|------|----------|
| VACUUM | 領域回収 | 自動/大量削除後 |
| VACUUM ANALYZE | 領域回収+統計更新 | 定期的に |
| REINDEX | インデックス再構築 | 性能劣化時 |
| ANALYZE | 統計情報のみ更新 | データ変更後 |

## 🔧 Git操作

### ブランチ管理

#### 🌳 Gitブランチとは？

**ブランチ = 開発の並行作業を可能にする仕組み**

```
main/develop ──┬─────────────────────→
               ├─ feature/login ────→ マージ
               └─ feature/dashboard → マージ
```

#### フィーチャーブランチの作成
```bash
git checkout -b feature/task-name
```

**コマンドの分解**：
- `checkout`：ブランチを切り替える
- `-b`：新規作成して切り替え
- `feature/`：機能開発用のプレフィックス

**命名規則の例**：
```bash
feature/add-user-settings      # 機能追加
fix/login-error                # バグ修正
refactor/optimize-query        # リファクタリング
docs/update-readme             # ドキュメント
```

#### 最新コードの取り込み

##### プル（Pull）方式
```bash
git checkout develop
git pull origin develop
git checkout feature/task-name
git merge develop
```

**メリット**：
- シンプルで分かりやすい
- マージコミットが履歴に残る

##### リベース（Rebase）方式
```bash
git checkout feature/task-name
git rebase develop
```

**メリット**：
- 履歴が直線的できれい
- コミット履歴が整理される

**リベースの動作**：
```
変更前：
develop: A─B─C
feature:     └─D─E

リベース後：
develop: A─B─C
feature:       └─D'─E'
```

**⚠️ 注意**：
- 公開済みブランチではリベースしない
- コンフリクトが発生しやすい

### コミット規約

#### 📝 Conventional Commitsとは？

**Conventional Commits = 統一されたコミットメッセージ規約**

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 基本的なコミットタイプ

```bash
git commit -m "feat: ユーザー設定画面を追加"
```

**主要なタイプ**：
| タイプ | 用途 | 例 |
|--------|------|-----|
| `feat` | 新機能追加 | feat: チーム管理機能を追加 |
| `fix` | バグ修正 | fix: ログイン時のエラーを修正 |
| `docs` | ドキュメント | docs: READMEにインストール手順を追加 |
| `style` | コード整形 | style: インデントを修正 |
| `refactor` | リファクタリング | refactor: 認証処理を共通化 |
| `test` | テスト | test: ユーザー登録のテストを追加 |
| `chore` | 雑務 | chore: 依存関係を更新 |

#### スコープ付きコミット

```bash
git commit -m "feat(auth): JWT認証を実装"
git commit -m "fix(api): タスク取得のN+1問題を解決"
```

**スコープの例**：
- `auth`：認証関連
- `api`：バックエンドAPI
- `ui`：フロントエンドUI
- `db`：データベース
- `deps`：依存関係

#### 詳細なコミットメッセージ

```bash
git commit
# エディタが開く
```

**記載例**：
```
feat(teams): チームメンバー招待機能を追加

- メールによる招待機能を実装
- 招待リンクの有効期限は7日間
- 重複招待のチェック機能も追加

Closes #123
```

#### コミットのベストプラクティス

**良い例** ✅：
```bash
git commit -m "fix: ユーザー一覧で削除済みユーザーが表示される問題を修正"
```
- 何を修正したか明確
- 問題の内容がわかる

**悪い例** ❌：
```bash
git commit -m "バグ修正"
git commit -m "update"
git commit -m "WIP"
```
- 内容が不明確
- 後で履歴を見ても理解できない

## 🛠️ トラブルシューティング用コマンド

### プロセス確認

#### 🔍 ポート使用状況の確認

##### 特定ポートの確認
```bash
lsof -i :3000      # フロントエンド
lsof -i :8000      # バックエンド
```

**lsofとは**：List Open Files（開いているファイルを表示）

**表示例**：
```
COMMAND   PID USER   FD   TYPE    DEVICE NODE NAME
node    12345 user   21u  IPv6 0x1234567      TCP *:3000 (LISTEN)
```

**エラー「ポートが既に使用されています」の対処**：
```bash
# 1. 使用中のプロセスを確認
lsof -i :3000

# 2. プロセスを終了
kill -9 12345  # PIDを指定
```

##### 全ポートの確認
```bash
netstat -tlnp      # Linux
netstat -an | grep LISTEN  # macOS
```

**表示の見方**：
```
Proto Local Address    State
tcp   0.0.0.0:3000    LISTEN  ← 3000番ポートで待機中
tcp   0.0.0.0:8000    LISTEN  ← 8000番ポートで待機中
```

#### 🔎 プロセスの確認

##### Dockerプロセス
```bash
ps aux | grep docker
```

**確認できること**：
- Dockerデーモンが起動しているか
- どのコンテナが実行中か

**結果の例**：
```
user  1234  0.5  2.3  /usr/bin/dockerd
user  5678  0.1  0.5  docker-compose up
```

##### Node.jsプロセス
```bash
ps aux | grep node
```

**異常な状態の例**：
```
user  9999  99.0  15.2  node /app/server.js
            ↑     ↑
         CPU使用率 メモリ使用率
```
- CPU 99%：無限ループの可能性
- メモリ15%超：メモリリークの可能性

##### Pythonプロセス
```bash
ps aux | grep python
```

**複数のPythonプロセス**：
```
user  1111  0.1  1.0  python -m uvicorn
user  2222  0.1  1.0  python -m uvicorn
user  3333  0.1  1.0  python -m uvicorn
user  4444  0.1  1.0  python -m uvicorn
```
→ gunicornの4ワーカー（正常）

### ディスク・メモリ確認

#### 💾 ディスク使用量

##### システム全体
```bash
df -h
```

**dfとは**：Disk Free（空き容量確認）
**-h**：Human readable（人間が読みやすい形式）

**表示例**：
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   45G   50G  48% /
/dev/sda2       500G  250G  225G  53% /home
```

**警告レベル**：
- 80%未満：安全 ✅
- 80-90%：注意 ⚠️
- 90%以上：危険 🚨

##### ディレクトリ別
```bash
du -sh *
```

**duとは**：Disk Usage（使用量確認）

**表示例**：
```
1.2G    node_modules
856M    .yarn
234M    backend
156M    frontend
45M     doc
```

**大きなディレクトリの調査**：
```bash
du -sh * | sort -rh | head -10
```
→ サイズ順に上位10個表示

##### Docker使用量
```bash
docker system df
```

**表示内容**：
```
TYPE          TOTAL   ACTIVE   SIZE      RECLAIMABLE
Images        15      5        3.45GB    2.1GB (60%)
Containers    8       5        125MB     45MB (36%)
Local Volumes 5       3        1.2GB     400MB (33%)
```

**クリーンアップ**：
```bash
docker system prune -a  # 未使用のイメージ等を削除
```

#### 🧠 メモリ使用量

##### システム全体（Linux）
```bash
free -h
```

**表示例**：
```
              total    used    free   shared  buff/cache   available
Mem:           16G     8.2G    2.1G     512M        5.7G        7.3G
Swap:          2G      0B      2G
```

**重要な値**：
- `used`：使用中のメモリ
- `available`：利用可能なメモリ（重要）
- `Swap`：スワップ使用（0が理想）

##### コンテナ別
```bash
docker stats
```

**リアルタイム表示**：
```
CONTAINER ID   NAME                CPU %   MEM USAGE / LIMIT     MEM %
abc123         team-insight-backend    2.5%    245MiB / 1GiB         23.9%
def456         team-insight-frontend   1.2%    156MiB / 512MiB      30.5%
ghi789         team-insight-postgres   0.8%    89MiB / 256MiB       34.8%
```

**異常の見分け方**：
- CPU% が常に100%近い → 処理が詰まっている
- MEM% が90%以上 → メモリ不足の可能性

### ログ検索

#### 🔍 エラーログの検索

##### ディレクトリ内検索
```bash
grep -r "ERROR" ./logs/
```

**grepオプション**：
- `-r`：再帰的に検索（サブディレクトリも）
- `-i`：大文字小文字を区別しない
- `-n`：行番号を表示

**より詳細な検索**：
```bash
grep -rn "ERROR" ./logs/ --include="*.log"
```

**検索結果の例**：
```
./logs/backend.log:152:ERROR: Database connection failed
./logs/backend.log:203:ERROR: Authentication token expired
./logs/frontend.log:45:ERROR: API request timeout
```

##### リアルタイムログ監視
```bash
tail -f logs/app.log | grep "ERROR"
```

**tailオプション**：
- `-f`：ファイルの更新を監視
- `-n 100`：最後の100行から表示

**複数の条件で検索**：
```bash
tail -f logs/app.log | grep -E "ERROR|WARNING|CRITICAL"
```

##### コンテナログの検索
```bash
docker-compose logs backend | grep "ERROR"
docker-compose logs --since "1h" | grep "timeout"
```

**時間指定オプション**：
- `--since "1h"`：1時間前から
- `--since "2024-01-15"`：特定日付から
- `--until "2024-01-16"`：特定日付まで

#### 📅 特定期間のログ（systemd）

```bash
journalctl --since "2024-01-01" --until "2024-01-02"
```

**journalctlとは**：systemdのログ管理ツール

**便利な時間指定**：
```bash
journalctl --since "1 hour ago"
journalctl --since "yesterday"
journalctl --since "2024-01-15 10:00" --until "2024-01-15 12:00"
```

**サービス別のログ**：
```bash
journalctl -u docker.service --since today
```

#### ログ検索のTips

**1. エラーの前後を確認**：
```bash
grep -B 5 -A 5 "ERROR" app.log
```
- `-B 5`：エラーの前5行
- `-A 5`：エラーの後5行

**2. エラーを数える**：
```bash
grep -c "ERROR" app.log
```

**3. エラーレベル別に集計**：
```bash
grep -E "ERROR|WARNING|INFO" app.log | cut -d' ' -f3 | sort | uniq -c
```

結果例：
```
   45 ERROR
  123 WARNING
  567 INFO
```

## 📝 便利なエイリアス設定

### 🎯 エイリアスとは？

**エイリアス = コマンドの短縮形（ショートカット）**

```
長いコマンド：docker-compose exec backend bash
     ↓
エイリアス：dce backend bash
```

### 設定方法

#### 1. 設定ファイルを開く
```bash
# Bashの場合
nano ~/.bashrc

# Zshの場合（Mac標準）
nano ~/.zshrc
```

#### 2. エイリアスを追加
```bash
# ファイルの最後に以下を追加
```

### Docker Compose用エイリアス

```bash
# 基本操作
alias dc='docker-compose'
alias dce='docker-compose exec'
alias dcl='docker-compose logs -f'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcp='docker-compose ps'

# 応用操作
alias dcr='docker-compose restart'
alias dcb='docker-compose build'
alias dcrb='docker-compose up -d --build'
```

**使用例**：
```bash
# 従来
docker-compose exec backend bash

# エイリアス使用
dce backend bash
```

### Team Insight専用エイリアス

```bash
# 起動・停止
alias ti-start='make start'
alias ti-stop='make stop'
alias ti-restart='make restart'
alias ti-status='make status'

# ログ確認
alias ti-logs='make logs'
alias ti-logs-be='make backend-logs'
alias ti-logs-fe='make frontend-logs'

# シェルアクセス
alias ti-shell='make backend-shell'
alias ti-shell-fe='make frontend-shell'
alias ti-psql='make db-shell'

# データベース操作
alias ti-migrate='make migrate'
alias ti-seed='make db-seed'

# 開発用
alias ti-test='make test'
alias ti-lint='make lint'
alias ti-types='make generate-types'
```

### Git用エイリアス

```bash
# 基本操作
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'

# ブランチ操作
alias gb='git branch'
alias gco='git checkout'
alias gcb='git checkout -b'

# ログ確認
alias glog='git log --oneline --graph --decorate'
alias gdiff='git diff'
```

### 便利な複合エイリアス

```bash
# 朝の作業開始
alias morning='git pull origin develop && make start && make status'

# 作業終了
alias eod='make stop && git status'

# フルリセット（注意！）
alias ti-reset='make clean && make setup'
```

### エイリアスの有効化

#### 3. 設定を反映
```bash
# Bashの場合
source ~/.bashrc

# Zshの場合
source ~/.zshrc
```

#### 4. 確認
```bash
# 登録されたエイリアスを確認
alias
```

### カスタマイズのヒント

**プロジェクトごとに切り替え**：
```bash
# プロジェクト切り替え関数
function project() {
  case $1 in
    ti)
      cd ~/projects/team-insight
      make status
      ;;
    other)
      cd ~/projects/other-project
      ;;
  esac
}

# 使用例
project ti  # Team Insightに移動
```

**頻繁に使うコマンドの組み合わせ**：
```bash
# テスト実行後に自動でカバレッジを開く
alias ti-test-cov='make test-coverage && open coverage/index.html'

# ログを見ながらサーバー再起動
alias ti-debug='make restart && make logs'
```

---

## 🎉 これで完成！

Team Insight ジュニアエンジニア向け実装ガイドのコマンドリファレンスが完成しました。

### 💡 最後のアドバイス

1. **まずは基本コマンドから**
   - `make start`、`make logs`、`make stop` をマスター
   - 慣れてきたらエイリアスを活用

2. **エラーが出たら**
   - エラーメッセージをよく読む
   - `make logs` でログを確認
   - このガイドのトラブルシューティングを参照

3. **分からないことがあったら**
   - このガイドを見返す
   - チームメンバーに質問
   - 一緒に解決方法を探す

頑張ってください！Team Insightの開発を楽しみましょう！ 🚀