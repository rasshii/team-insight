# プロジェクト概要と開発環境セットアップ

**このガイドで学べること**：
- Team Insightプロジェクトの目的と価値
- 開発に必要なツールの基本的な使い方（Docker、Git、Make）
- 開発環境の構築手順（Docker Compose）
- 最初の動作確認方法

## 📌 Team Insightとは

### プロジェクトの背景

Team Insightは、**Backlogのデータを活用してチームの生産性を可視化・分析するWebアプリケーション**です。

#### Backlogとは？
Backlogは日本のヌーラボ社が提供するプロジェクト管理ツールで、以下の機能を提供しています：
- 課題管理（タスク管理）
- プロジェクト管理
- Wiki機能
- Git/SVN連携
- ガントチャート

### なぜTeam Insightが必要なのか？

Backlogは優れたツールですが、以下の課題があります：

1. **分析機能の不足**: チーム全体の生産性を俯瞰的に見る機能が限定的
2. **個人のパフォーマンス可視化が困難**: 個人の成長や改善点を把握しづらい
3. **ボトルネックの特定が困難**: プロジェクトの問題点を見つけるのに時間がかかる

Team Insightはこれらの課題を解決し、データドリブンな意思決定を支援します。

### 主な機能（実装状況）

#### ✅ 実装済み
- Backlog OAuth認証によるログイン
- ユーザー・プロジェクト・タスクデータの同期
- 個人ダッシュボード（KPI表示、タスク履歴）
- チーム管理機能
- ユーザー管理機能（RBAC対応）
- レポート配信機能

#### 🚧 実装中
- チーム生産性ダッシュボード
- 自動同期スケジューラー

#### 📋 未実装
- プロジェクトダッシュボード（詳細分析）
- 組織ダッシュボード
- 高度な分析機能（ボトルネック検出、サイクルタイム分析）

### データフロー概要

```mermaid
graph LR
    subgraph Backlog["Backlog（外部）"]
        BProjects["プロジェクトデータ"]
        BTasks["タスクデータ"]
        BUsers["ユーザーデータ"]
    end
    
    subgraph TeamInsight["Team Insight"]
        subgraph Frontend["フロントエンド"]
            Dashboard["ダッシュボード"]
            Reports["レポート"]
            Settings["設定"]
        end
        
        subgraph Backend["バックエンド"]
            API["FastAPI"]
            Sync["同期サービス"]
            Analytics["分析エンジン"]
            Auth["認証サービス"]
        end
        
        subgraph Storage["ストレージ"]
            DB[(PostgreSQL)]
            Cache[(Redis)]
        end
    end
    
    subgraph User["ユーザー"]
        Browser["ブラウザ"]
        Email["メール"]
    end
    
    Browser -->|アクセス| Dashboard
    Dashboard -->|データ取得| API
    API -->|データ読み込み| DB
    API -->|キャッシュ| Cache
    
    Sync -->|API呼び出し| BProjects
    Sync -->|API呼び出し| BTasks
    Sync -->|API呼び出し| BUsers
    Sync -->|保存| DB
    
    Analytics -->|データ分析| DB
    Analytics -->|レポート生成| Reports
    Reports -->|メール送信| Email
    
    Auth -->|OAuth| Backlog
    
    style BProjects fill:#f9f
    style BTasks fill:#f9f
    style BUsers fill:#f9f
    style DB fill:#f96
    style Cache fill:#f96
```

## 🛠️ 開発に必要なツールの理解

### Docker（ドッカー）とは？

**Docker**は、アプリケーションを「コンテナ」という単位で動かすためのツールです。

#### 📦 コンテナを日常生活で例えると

```
従来の開発環境：
「新しいアパートに引っ越して、家具や家電を一から揃える」
- 時間がかかる
- 環境によって合わないものがある
- 他の人と同じ環境を作るのが大変

Dockerコンテナ：
「家具付きのホテルに泊まる」
- 必要なものがすべて揃っている
- どこでも同じ環境が作れる
- チェックアウトすれば元の状態に戻る
```

#### なぜDockerが必要？
1. **環境の統一**: 「私のPCでは動くけど、あなたのPCでは動かない」問題を解決
2. **簡単なセットアップ**: 複雑な環境構築をワンコマンドで実行
3. **独立した環境**: プロジェクトごとに異なるバージョンのソフトウェアを使える

#### Docker基本コマンド
```bash
# Dockerが正しくインストールされているか確認
docker --version
# 出力例: Docker version 24.0.6, build ed223bc

# 実行中のコンテナを表示
docker ps
# 出力例:
# CONTAINER ID   IMAGE           COMMAND       CREATED       STATUS       PORTS
# abc123def456   team-insight    "npm start"   2 hours ago   Up 2 hours   3000->3000/tcp

# コンテナのログを見る（リアルタイム）
docker logs -f team-insight-frontend-1

# コンテナの中に入る（デバッグ用）
docker exec -it team-insight-backend-1 bash
# コンテナ内でのコマンド例:
# ls -la  # ファイル一覧
# python --version  # Pythonバージョン確認
# exit  # コンテナから抜ける
```

### Docker Composeとは？

**Docker Compose**は、複数のコンテナをまとめて管理するツールです。

#### Team Insightのコンテナ構成

```mermaid
graph TB
    subgraph Docker Compose
        nginx[Nginx<br/>Port: 80]
        frontend[Frontend<br/>Next.js<br/>Port: 3000]
        backend[Backend<br/>FastAPI<br/>Port: 8000]
        postgres[(PostgreSQL<br/>Port: 5432)]
        redis[(Redis<br/>Port: 6379)]
        mailhog[MailHog<br/>Port: 8025]
    end
    
    User[ユーザー] -->|http://localhost| nginx
    nginx -->|/api/*| backend
    nginx -->|/*| frontend
    backend --> postgres
    backend --> redis
    backend --> mailhog
    
    style nginx fill:#f9f
    style frontend fill:#bbf
    style backend fill:#bfb
    style postgres fill:#f96
    style redis fill:#f66
    style mailhog fill:#ff9
```

#### docker-compose.ymlの実際の構成

```yaml
# docker-compose.ymlの主要部分
version: '3.8'

services:
  # Nginx（リバースプロキシ）
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"  # ホストの80番ポートをコンテナの80番に接続
    depends_on:
      - frontend
      - backend

  # フロントエンド（Next.js）
  frontend:
    build: 
      context: ./frontend
      dockerfile: ../infrastructure/docker/frontend/Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost
    volumes:
      - ./frontend:/app  # ソースコードをマウント（ホットリロード対応）

  # バックエンド（FastAPI）
  backend:
    build:
      context: ./backend
      dockerfile: ../infrastructure/docker/backend/Dockerfile
    env_file:
      - ./backend/.env  # 環境変数ファイルを読み込み
    depends_on:
      postgres:
        condition: service_healthy  # PostgreSQLが健全になってから起動

  # データベース（PostgreSQL）
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=teaminsight
      - POSTGRES_USER=teaminsight
      - POSTGRES_PASSWORD=teaminsight
    volumes:
      - postgres_data:/var/lib/postgresql/data  # データ永続化
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U teaminsight"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:  # 名前付きボリューム（データ保存用）
  redis_data:
```

**💁 ポイント**:
- `depends_on`: コンテナの起動順序を制御
- `volumes`: ファイルの永続化やホットリロードを実現
- `env_file`: 環境変数を外部ファイルから読み込み
- `healthcheck`: コンテナの健康状態を確認

### Git（ギット）とは？

**Git**は、コードの変更履歴を管理するバージョン管理システムです。

#### なぜGitが必要？
1. **変更履歴の追跡**: いつ、誰が、何を変更したかを記録
2. **チーム開発**: 複数人で同時に開発できる
3. **バックアップ**: コードを安全に保管
4. **実験的な変更**: ブランチを使って安全に新機能を試せる

#### Git基本コマンド
```bash
# Gitが正しくインストールされているか確認
git --version

# リポジトリの状態を確認
git status

# 変更内容を確認
git diff

# 変更をステージング（コミット準備）
git add [ファイル名]
git add .  # すべての変更をステージング

# コミット（変更を記録）
git commit -m "変更内容の説明"

# リモートリポジトリから最新を取得
git pull

# リモートリポジトリに変更をプッシュ
git push
```

### Make（メイク）とは？

**Make**は、複雑なコマンドを簡単に実行するためのツールです。

#### なぜMakeが必要？
1. **コマンドの簡略化**: 長いコマンドを短いコマンドで実行
2. **タスクの自動化**: 複数のコマンドをまとめて実行
3. **一貫性**: チーム全員が同じコマンドを使える

#### Team Insightでのメインコマンド

**基本コマンド**:
```bash
# ヘルプを表示（使用可能なコマンド一覧）
make help

# 初回セットアップ（環境構築 + DB初期化）
make setup

# 全サービスを起動
make start

# 全サービスを停止
make stop

# サービスの状態を確認
make status
```

**ログ確認コマンド**:
```bash
# 全サービスのログを表示
make logs

# 特定サービスのログ
make frontend-logs  # フロントエンド
make backend-logs   # バックエンド
make db-logs        # データベース
```

**コンテナへのアクセス**:
```bash
# コンテナ内でコマンドを実行
make frontend-shell  # フロントエンドコンテナ
make backend-shell   # バックエンドコンテナ
make db-shell        # PostgreSQLコンテナ
```

**💁 ポイント**: Team Insightでは、ほとんどの操作を`make`コマンド経由で実行できます。
`docker-compose`を直接使う必要はありません！

## 🚀 開発環境セットアップ

### 前提条件

開発を始める前に、以下のツールがインストールされていることを確認してください：

1. **Docker Desktop** (必須)
   - Mac: https://www.docker.com/products/docker-desktop
   - Windows: WSL2を有効化してからインストール
   - Linux: Docker EngineとDocker Compose
   - インストール後、Docker Desktopを起動

2. **Git** (必須)
   - Mac: `brew install git` または Xcodeコマンドラインツール
   - Windows: https://git-scm.com/download/win
   - Linux: `sudo apt-get install git` (Ubuntu/Debian)
   - 確認: `git --version`

3. **Make** (必須)
   - Mac: 標準でインストール済み
   - Windows: WSL2内で `sudo apt-get install make`
   - Linux: `sudo apt-get install make`
   - 確認: `make --version`

4. **推奨エディタ**
   - VS Code（拡張機能: Python, TypeScript, Docker）
   - または任意のコードエディタ

### セットアップ手順（ステップバイステップ）

#### ステップ1: リポジトリのクローン

まず、プロジェクトのコードを自分のPCにダウンロードします。

```bash
# ターミナル（コマンドプロンプト）を開いて実行
# プロジェクトを置きたいディレクトリに移動
cd ~/Desktop  # または任意のディレクトリ

# リポジトリをクローン（コピー）
git clone <repository-url>

# プロジェクトディレクトリに移動
cd team-insight

# ディレクトリ構造を確認
ls -la
```

**💡 解説**: 
- `git clone`は、リモートリポジトリ（GitHub等）からローカルにコードをコピーします
- `cd`（change directory）でディレクトリを移動します
- `ls -la`で現在のディレクトリの内容を表示します

#### ステップ2: 環境変数の設定

環境変数は、アプリケーションの設定情報（APIキー、データベース接続情報など）を保存するファイルです。

```bash
# バックエンド環境変数のテンプレートをコピー
cp backend/.env.example backend/.env

# フロントエンド環境変数のテンプレートをコピー
cp frontend/.env.example frontend/.env

# ファイルが作成されたか確認
ls backend/.env frontend/.env
```

**💡 解説**: 
- `.env.example`は環境変数のテンプレート（見本）ファイル
- `cp`（copy）コマンドでファイルをコピー
- `.env`ファイルには実際の設定値を入力します

#### ステップ3: 環境変数の編集

VS Codeまたはテキストエディタで`backend/.env`を開いて編集します。

```bash
# VS Codeで開く場合
code backend/.env

# または、nanoエディタで開く場合
nano backend/.env
```

以下の値を設定してください：

```bash
# ===== 必須設定 =====
# Backlog OAuth設定
BACKLOG_CLIENT_ID=your-client-id      # 例: abc123def456
BACKLOG_CLIENT_SECRET=your-secret      # 例: xyz789uvw012
BACKLOG_SPACE_KEY=your-space          # 例: mycompany
BACKLOG_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback

# 初期管理者メールアドレス
INITIAL_ADMIN_EMAILS=your-email@example.com  # 例: admin@mycompany.com

# ===== その他の設定（変更不要）=====
# データベース接続（Docker内部で使用）
DATABASE_URL=postgresql://teaminsight:teaminsight@postgres:5432/teaminsight

# Redis接続（Docker内部で使用）
REDIS_URL=redis://redis:6379/0

# セキュリティキー（開発環境用のデフォルト値）
SECRET_KEY=your-secret-key-here

# アプリケーション設定
APP_NAME="Team Insight"
DEBUG=true
```

**💡 Backlog OAuth アプリの作成方法（詳細）**:

1. **Backlogにログイン**
   - ブラウザで`https://[your-space].backlog.jp`にアクセス
   - 管理者権限のあるアカウントでログイン

2. **OAuth アプリケーションの設定画面へ**
   - 右上の歯車アイコン → 「スペース設定」をクリック
   - 左メニューの「アプリケーション」をクリック
   - 「OAuth2」タブを選択

3. **新規アプリケーションを作成**
   - 「新しいアプリケーションを追加」ボタンをクリック
   - 以下の情報を入力：
     - **アプリケーション名**: Team Insight
     - **説明**: チーム生産性分析ツール
     - **リダイレクトURI**: `http://localhost:8000/api/v1/auth/callback`
   - 「追加」ボタンをクリック

4. **クライアントIDとシークレットをコピー**
   - 作成後に表示される「クライアントID」と「クライアントシークレット」をコピー
   - これらを`.env`ファイルに貼り付け

#### ステップ4: Docker環境の起動

Docker Desktopが起動していることを確認してから、以下のコマンドを実行します。

```bash
# 初回起動（セットアップを含む）
make setup

# このコマンドは以下の処理を実行します：
# 1. 必要なDockerイメージをダウンロード
# 2. カスタムイメージをビルド
# 3. データベースを初期化
# 4. すべてのサービスを起動
```

**💡 初回起動時に何が起きているか？**

1. **Dockerイメージのダウンロード** (1-3分)
   ```
   Pulling postgres (postgres:15)...
   Pulling redis (redis:7.0.11-alpine)...
   Pulling nginx (nginx:1.24-alpine)...
   ```
   - PostgreSQL、Redis、Nginxの公式イメージをダウンロード

2. **カスタムイメージのビルド** (3-5分)
   ```
   Building frontend...
   Step 1/10 : FROM node:18-alpine
   Step 2/10 : WORKDIR /app
   ...
   Building backend...
   Step 1/12 : FROM python:3.11-slim
   Step 2/12 : WORKDIR /app
   ...
   ```
   - フロントエンドとバックエンドのDockerイメージを作成
   - 必要なライブラリをインストール

3. **サービスの起動**
   ```
   Creating network "team-insight_default"
   Creating team-insight_postgres_1 ... done
   Creating team-insight_redis_1    ... done
   Creating team-insight_backend_1  ... done
   Creating team-insight_frontend_1 ... done
   Creating team-insight_nginx_1    ... done
   ```

**通常の起動（2回目以降）**
```bash
# すでにビルド済みの場合
make start

# 停止する場合
make stop

# 再起動する場合
make restart
```

#### ステップ5: 起動確認

サービスが正しく起動しているか確認します。

```bash
# サービスの状態確認
make status

# 以下のような出力が表示されます：
# NAME                      STATUS    PORTS
# team-insight-nginx-1      running   0.0.0.0:80->80/tcp
# team-insight-frontend-1   running   3000/tcp
# team-insight-backend-1    running   8000/tcp
# team-insight-postgres-1   running   5432/tcp
# team-insight-redis-1      running   6379/tcp
# team-insight-mailhog-1    running   0.0.0.0:8025->8025/tcp
```

**ログの確認方法**
```bash
# すべてのサービスのログを表示（リアルタイム）
make logs

# 特定のサービスのログを表示
make backend-logs   # バックエンドのログ
make frontend-logs  # フロントエンドのログ
make db-logs        # データベースのログ

# ログの見方：
# [サービス名] | [時刻] [ログレベル] メッセージ
# backend_1    | 2024-01-20 10:00:00 INFO: Application startup complete
```

**💡 よくあるログメッセージ**
- `INFO: Application startup complete` - アプリケーションが正常に起動
- `INFO: Uvicorn running on http://0.0.0.0:8000` - バックエンドAPIが起動
- `ready - started server on 0.0.0.0:3000` - フロントエンドが起動
- `database system is ready to accept connections` - データベースが準備完了

### 初回ログインと管理者設定（詳細手順）

#### ステップ1: アプリケーションへアクセス

1. **ブラウザを開く**
   - Chrome、Firefox、Safari、Edgeなど任意のブラウザ

2. **URLを入力**
   ```
   http://localhost
   ```

   **⚠️ 重要な注意点**:
   - ポート番号なしの`http://localhost`を使用
   - 以下は間違い：
     - ❌ `http://localhost:3000`（フロントエンド直接アクセス - CORSエラーになる）
     - ❌ `http://localhost:8000`（バックエンド直接アクセス - UIが表示されない）
   - ✅ `http://localhost`（Nginx経由 - 正しいアクセス方法）

3. **ログイン画面が表示される**
   - Team Insightのロゴとログインボタンが表示されます

#### ステップ2: Backlogでログイン

1. **「Backlogでログイン」ボタンをクリック**
   - Backlogの認証画面にリダイレクトされます
   - URLが`https://[your-space].backlog.jp/OAuth2/authorize`に変わります

2. **Backlogアカウントでログイン**
   - メールアドレスとパスワードを入力
   - または、すでにログイン済みの場合は次のステップへ

3. **アプリケーション連携を承認**
   - 「Team Insightがあなたのアカウント情報にアクセスすることを許可しますか？」と表示される
   - 「許可する」ボタンをクリック

4. **Team Insightに戻る**
   - 自動的にTeam Insightにリダイレクトされます
   - ダッシュボードが表示されます

#### ステップ3: 管理者権限の設定（重要）

Team Insightでは、セキュリティのため、最初のユーザーも自動的に管理者にはなりません。以下の手順で管理者権限を設定します。

1. **RBACシステムの初期化**（初回のみ必要）
   ```bash
   # ロール（役割）とパーミッション（権限）の初期データを投入
   docker-compose exec backend python scripts/init_rbac.py
   
   # 成功すると以下のメッセージが表示されます：
   # RBAC初期化を開始します...
   # ロールを作成しました: ADMIN
   # ロールを作成しました: PROJECT_LEADER
   # ロールを作成しました: MEMBER
   # 権限を設定しました...
   # RBAC初期化が完了しました！
   ```

2. **自分を管理者に設定**
   ```bash
   # 方法1: Makeコマンドを使用（推奨）
   make init-admin
   
   # 方法2: 環境変数を直接指定
   docker-compose exec backend bash -c "INITIAL_ADMIN_EMAILS=your-email@example.com python scripts/init_admin.py"
   
   # 方法3: 個別にロールを付与
   make set-admin EMAIL=your-email@example.com
   ```

   **💡 補足説明**:
   - `docker-compose exec`: Dockerコンテナ内でコマンドを実行
   - `backend`: バックエンドコンテナを指定
   - `python scripts/init_admin.py`: 管理者初期化スクリプトを実行
   - `INITIAL_ADMIN_EMAILS`: 環境変数で管理者のメールアドレスを指定

3. **設定確認**
   ```bash
   # 現在のユーザーとロールを確認
   make list-users
   
   # 以下のような出力が表示されます：
   # ===== ユーザー一覧 =====
   # Email: your-email@example.com
   # Name: Your Name
   # Active: True
   # Global Roles: ADMIN
   # Project Roles: なし
   # ========================
   ```

## 🔍 最初の動作確認（詳細）

### 管理機能の確認

管理者権限設定後、実際に管理機能が使えるか確認しましょう。

#### 1. ユーザー管理画面

1. **アクセス方法**
   - ブラウザで http://localhost/admin/users にアクセス
   - または、ナビゲーションバーの「管理」→「ユーザー」をクリック

2. **確認ポイント**
   - ユーザー一覧テーブルが表示される
   - 自分のユーザーに「ADMIN」バッジが付いている
   - 「Backlogから同期」ボタンが表示されている

3. **Backlogユーザーの同期**
   ```
   「Backlogから同期」ボタンをクリック
   ↓
   確認ダイアログで「同期」をクリック
   ↓
   Backlogスペースの全ユーザーがインポートされる
   ↓
   成功メッセージ: "X名のユーザーを同期しました"
   ```

#### 2. チーム管理画面

1. **アクセス方法**
   - http://localhost/admin/teams にアクセス

2. **新しいチームを作成**
   ```
   「新規チーム」ボタンをクリック
   ↓
   チーム名: "開発チーム"
   説明: "フロントエンド・バックエンド開発"
   ↓
   「作成」ボタンをクリック
   ```

3. **チームメンバーを追加**
   - チーム名をクリックして詳細画面へ
   - 「メンバーを追加」ボタンをクリック
   - ユーザーを選択して追加

#### 3. 個人ダッシュボード

1. **アクセス方法**
   - http://localhost/dashboard/personal
   - または、ナビゲーションの「ダッシュボード」→「個人」

2. **表示される情報**
   - 今月の完了タスク数
   - 平均完了時間
   - タスクの種類別分布
   - 最近の活動履歴

### 開発ツールの詳細な使い方

#### 1. FastAPI自動ドキュメント（Swagger UI）

1. **アクセス**
   ```
   http://localhost/api/v1/docs
   ```

2. **主な機能**
   - **エンドポイント一覧**: すべてのAPIが階層的に表示
   - **Try it out**: 実際にAPIを実行できる
   - **スキーマ**: リクエスト/レスポンスの型を確認

3. **APIを試す手順**
   ```
   1. 試したいエンドポイントをクリック（例: GET /api/v1/users/me）
   2. 「Try it out」ボタンをクリック
   3. 必要なパラメータを入力
   4. 「Execute」ボタンをクリック
   5. レスポンスが下に表示される
   ```

#### 2. データベースの操作

1. **PostgreSQLに接続**
   ```bash
   # データベースシェルに入る
   make db-shell
   
   # または直接コマンド
   docker-compose exec postgres psql -U teaminsight -d teaminsight
   ```

2. **よく使うPostgreSQLコマンド**
   ```sql
   -- 現在のスキーマを確認
   \dn
   
   -- team_insightスキーマのテーブル一覧
   \dt team_insight.*
   
   -- 特定のテーブルの構造を確認
   \d team_insight.users
   
   -- ユーザー一覧を表示
   SELECT id, email, name, is_active FROM team_insight.users;
   
   -- ユーザーのロールを確認
   SELECT u.email, r.name as role 
   FROM team_insight.users u
   JOIN team_insight.user_roles ur ON u.id = ur.user_id
   JOIN team_insight.roles r ON ur.role_id = r.id;
   
   -- データベースシェルを抜ける
   \q
   ```

3. **データベースのバックアップ**
   ```bash
   # バックアップを作成
   make db-backup
   
   # バックアップファイルは ./backups/ に保存される
   ```

#### 3. Redisキャッシュの操作

1. **Redisの状態確認**
   ```bash
   # すべてのキーを表示
   make redis-keys
   
   # 出力例：
   # 1) "cache:api:/api/v1/projects:user:123"
   # 2) "session:abc123def456"
   # 3) "rate_limit:login:user@example.com"
   ```

2. **Redisシェルに接続**
   ```bash
   # Redisシェルに入る
   docker-compose exec redis redis-cli
   
   # よく使うRedisコマンド
   > KEYS *              # すべてのキーを表示
   > GET key_name        # 特定のキーの値を取得
   > TTL key_name        # キーの有効期限を確認
   > FLUSHALL           # すべてのキャッシュをクリア（注意！）
   > exit               # Redisシェルを抜ける
   ```

3. **キャッシュのクリア**
   ```bash
   # Makeコマンドで簡単にクリア
   make redis-flush
   ```

#### 4. ログの詳細な確認方法

1. **特定の文字列でログを検索**
   ```bash
   # エラーログのみ表示
   make logs | grep ERROR
   
   # 特定のユーザーに関するログ
   make backend-logs | grep "user@example.com"
   
   # 直近100行のログ
   make backend-logs | tail -100
   ```

2. **ログファイルの保存**
   ```bash
   # ログをファイルに保存
   make logs > logs_$(date +%Y%m%d_%H%M%S).txt
   ```

## 💡 学習のポイント

### 1. システムの全体像を理解する

まずは以下の流れを理解しましょう：
1. ユーザーがブラウザでアクセス
2. Nginx経由でリクエストが振り分けられる
3. 認証が必要な場合はBacklog OAuthへ
4. APIリクエストはFastAPIで処理
5. データはPostgreSQLに保存
6. キャッシュはRedisで管理

### 2. ログを活用する

問題が発生したら、まずログを確認：
```bash
# エラーが出た場合
make logs | grep ERROR

# 特定のサービスのログ
make backend-logs | tail -f
```

### 3. 実際のコードを確認

- **バックエンド**: `backend/app/main.py`から開始
- **フロントエンド**: `frontend/src/app/page.tsx`から開始
- **API定義**: `backend/app/api/v1/`ディレクトリ

### 次のステップ

環境構築が完了したら、[アーキテクチャと技術スタック](02-architecture.md)に進んで、システムの詳細な構成を学びましょう。

## トラブルシューティング（詳細ガイド）

### よくある問題と解決方法

#### 1. ポート競合エラー

**症状**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use
```

**原因**: 他のアプリケーションが同じポートを使用している

**解決方法**:
```bash
# 使用中のポートを確認（Mac/Linux）
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL
lsof -i :80    # Nginx

# Windowsの場合
netstat -ano | findstr :3000

# プロセスを終了（Mac/Linux）
kill -9 [PID]  # PIDは上記コマンドで確認した番号

# または、Docker Desktopを再起動
```

#### 2. Dockerビルドエラー

**症状**:
```
ERROR: failed to solve: failed to fetch anonymous token
```

**解決方法**:
```bash
# Docker Desktopが起動しているか確認

# キャッシュをクリアして再ビルド
docker system prune -a  # 注意：すべてのDockerイメージを削除
make rebuild

# ネットワークの問題の場合
docker network prune
```

#### 3. 認証エラー（Backlog OAuth）

**症状**: 「認証に失敗しました」または「スペースが許可されていません」

**確認事項**:
1. **環境変数の確認**
   ```bash
   # .envファイルの内容を確認（シークレットは隠して）
   cat backend/.env | grep BACKLOG
   
   # 確認ポイント：
   # - BACKLOG_CLIENT_ID が正しいか
   # - BACKLOG_CLIENT_SECRET が正しいか
   # - BACKLOG_SPACE_KEY がBacklogのスペースIDと一致しているか
   # - BACKLOG_REDIRECT_URI が正確に http://localhost:8000/api/v1/auth/callback か
   ```

2. **Backlog側の設定確認**
   - Backlogの管理画面でOAuthアプリの設定を再確認
   - リダイレクトURIが完全一致しているか（末尾のスラッシュも含めて）

#### 4. データベース接続エラー

**症状**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解決方法**:
```bash
# PostgreSQLコンテナの状態確認
docker-compose ps postgres

# ログを確認
make db-logs

# データベースを再起動
docker-compose restart postgres

# それでも解決しない場合、ボリュームを削除して再作成
docker-compose down -v  # 注意：データが削除される
make setup
```

#### 5. フロントエンドが表示されない

**症状**: http://localhost にアクセスしても画面が表示されない

**確認事項**:
```bash
# Nginxの状態確認
docker-compose ps nginx

# Nginxのログ確認
make nginx-error-log

# フロントエンドのビルド状態確認
make frontend-logs | grep -E "(error|Error|ERROR)"

# 正しいURLでアクセスしているか確認
# ✅ http://localhost
# ❌ http://localhost:3000
```

#### 6. "make: command not found" エラー

**症状**: Makeコマンドが使えない

**解決方法**:
```bash
# Mac
brew install make

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install make

# Windows (WSL2内で実行)
sudo apt-get install make

# 直接docker-composeコマンドを使う場合
docker-compose up -d  # make start の代わり
docker-compose down   # make stop の代わり
```

#### 7. メモリ不足エラー

**症状**: 
```
The build failed because the process exited too early
```

**解決方法**:
1. Docker Desktopの設定を開く
2. Resources → Advanced
3. Memoryを4GB以上に設定
4. Applyをクリックして再起動

#### 8. 管理者権限が付与されない

**症状**: `make init-admin`を実行しても管理者にならない

**確認事項**:
```bash
# RBACが初期化されているか確認
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.role import Role
db = SessionLocal()
roles = db.query(Role).all()
print([r.name for r in roles])
"

# 出力が空の場合、RBACを初期化
docker-compose exec backend python scripts/init_rbac.py

# メールアドレスが正しいか確認
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f'{u.email} - Active: {u.is_active}')
"
```

### デバッグのヒント

1. **ログレベルを上げる**
   ```bash
   # backend/.envを編集
   LOG_LEVEL=DEBUG
   
   # 再起動
   make restart
   ```

2. **コンテナの中に入って調査**
   ```bash
   # バックエンドコンテナに入る
   docker-compose exec backend bash
   
   # Pythonシェルを起動
   python
   >>> from app.db.session import SessionLocal
   >>> from app.models.user import User
   >>> db = SessionLocal()
   >>> users = db.query(User).all()
   >>> print(len(users))
   ```

3. **ネットワークの確認**
   ```bash
   # コンテナ間の通信を確認
   docker-compose exec frontend ping backend
   docker-compose exec backend ping postgres
   ```

### それでも解決しない場合

1. **完全リセット**（最終手段）
   ```bash
   # すべてを停止・削除
   make clean
   
   # Dockerイメージも削除
   docker system prune -a
   
   # 最初からやり直し
   make setup
   ```

2. **ログをすべて保存して共有**
   ```bash
   # ログを収集
   make logs > debug_logs.txt 2>&1
   docker-compose ps >> debug_logs.txt
   cat backend/.env | grep -v SECRET >> debug_logs.txt
   ```

---

📝 **重要**: エラーメッセージは必ず**全文をコピー**して保存しましょう。エラーメッセージの一部だけでは原因を特定できないことがあります。

💡 **ヒント**: 多くの問題は以下で解決します：
1. Docker Desktopの再起動
2. `make restart`でサービスの再起動
3. ブラウザのキャッシュクリア（Ctrl+Shift+R）