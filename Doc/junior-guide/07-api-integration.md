# API連携の実装方法

**このガイドで学べること**：
- APIとREST APIの基本概念から理解
- HTTPメソッドとJSONデータ形式の基礎
- Backlog APIとの連携実装方法
- 非同期処理とエラーハンドリングの基本
- データ同期戦略とスケジューリングの実装
- レート制限とリトライ処理の実装

## 🌟 はじめに：APIとは？

### 📡 APIを日常生活で例えると

**API（Application Programming Interface）= アプリケーション同士が会話するための窓口**

```
レストランで例えると：
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   お客様     │     │  ウェイター  │     │   厨房      │
│ （あなたの   │ ←→ │   （API）    │ ←→ │ （Backlog）  │
│  アプリ）    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘

1. 注文する（リクエスト）
2. ウェイターが厨房に伝える
3. 料理が来る（レスポンス）
```

### 🔌 REST APIとは？

REST API = Webの仕組みを使ったAPI

**特徴**：
1. **URL（住所）でリソースを指定**
   - `https://api.example.com/users` = ユーザー一覧
   - `https://api.example.com/users/123` = ID:123のユーザー

2. **HTTPメソッドで操作を指定**
   - GET = 取得（読む）
   - POST = 作成（新規追加）
   - PUT = 更新（書き換え）
   - DELETE = 削除

3. **JSONでデータをやり取り**

### 📋 HTTPメソッドの基本

| メソッド | 意味 | 例 | 現実世界の例 |
|---------|------|-----|-------------|
| GET | データを取得 | ユーザー情報を見る | 本を読む |
| POST | データを作成 | 新規ユーザー登録 | 手紙を投函 |
| PUT | データを更新 | プロフィール編集 | 文書を書き換え |
| DELETE | データを削除 | アカウント削除 | ゴミ箱に捨てる |

### 📄 JSONとは？

**JSON（JavaScript Object Notation）= データを表現する形式**

```json
// JSONの例：ユーザー情報
{
  "id": 123,
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "is_active": true,
  "roles": ["admin", "user"],
  "profile": {
    "age": 30,
    "city": "東京"
  }
}
```

**JSONの基本ルール**：
- `{}` : オブジェクト（辞書型）
- `[]` : 配列（リスト）
- `""` : 文字列
- 数値 : そのまま書く
- `true/false` : 真偽値
- `null` : 空値

## ⚡ 非同期処理の基本

### 同期処理 vs 非同期処理

```python
# 同期処理（1つずつ順番に実行）
def sync_example():
    task1()  # 3秒かかる
    task2()  # 2秒かかる
    task3()  # 1秒かかる
    # 合計: 6秒

# 非同期処理（同時並行で実行）
async def async_example():
    await asyncio.gather(
        task1(),  # 3秒
        task2(),  # 2秒  → 同時実行
        task3()   # 1秒
    )
    # 合計: 3秒（最も長いタスクの時間）
```

**非同期処理のメリット**：
- API呼び出しの待ち時間を有効活用
- 複数のAPIを同時に呼べる
- アプリケーション全体の応答性が向上

### async/awaitの基本

```python
# asyncで非同期関数を定義
async def get_user_data(user_id: int):
    # awaitで非同期処理の完了を待つ
    response = await httpx.get(f"https://api.example.com/users/{user_id}")
    return response.json()

# 非同期関数の呼び出し
async def main():
    user_data = await get_user_data(123)
    print(user_data)
```

## 🌐 Backlog API概要

### Backlog APIとは

BacklogはREST APIを提供しており、以下の操作が可能です：
- プロジェクト情報の取得・更新
- 課題（タスク）の取得・作成・更新
- ユーザー情報の取得
- ファイルのアップロード・ダウンロード
- Wiki、Git連携など

### APIエンドポイント構造

```
https://{space_key}.backlog.com/api/v2/{リソース}

例：
https://example.backlog.com/api/v2/projects      # プロジェクト一覧
https://example.backlog.com/api/v2/issues        # 課題一覧
https://example.backlog.com/api/v2/users         # ユーザー一覧
```

### 認証方法

Backlog APIの認証には2つの方法があります：

1. **APIキー認証**（シンプル）
   ```
   https://example.backlog.com/api/v2/projects?apiKey=YOUR_API_KEY
   ```

2. **OAuth 2.0認証**（Team Insightで採用）
   ```
   Authorization: Bearer YOUR_ACCESS_TOKEN
   ```

## 🏗️ BacklogClientの実装

### 🔧 クライアントクラスの設計

```python
# backend/app/services/backlog_client.py
import httpx  # 非同期HTTPクライアントライブラリ
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class BacklogClient:
    """
    Backlog APIクライアント
    
    責務：
    - Backlog APIへのHTTPリクエスト
    - 認証ヘッダーの管理
    - エラーハンドリングとリトライ
    - レート制限の対応
    """
    
    def __init__(self, access_token: str):
        """
        クライアントの初期化
        
        Args:
            access_token: OAuth 2.0のアクセストークン
        """
        self.access_token = access_token
        # ベースURLを構築（スペースキーを使用）
        self.base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.com/api/v2"
        # 共通ヘッダー
        self.headers = {
            "Authorization": f"Bearer {access_token}",  # Bearer認証
            "Content-Type": "application/json"          # JSON形式
        }

### 🚨 エラーハンドリングとリトライ処理

```python
    async def _make_request(
        self,
        method: str,              # HTTPメソッド（GET, POST, PUT, DELETE）
        endpoint: str,            # エンドポイント（例: "projects"）
        params: Optional[Dict] = None,     # URLパラメータ
        json_data: Optional[Dict] = None,  # リクエストボディ
        retry_count: int = 3      # リトライ回数
    ) -> Any:
        """
        APIリクエストの共通処理
        
        エラーハンドリングの戦略：
        1. ネットワークエラー → リトライ
        2. レート制限（429） → 指定時間待機後リトライ
        3. サーバーエラー（5xx） → リトライ
        4. クライアントエラー（4xx） → 即座に例外
        """
        
        url = f"{self.base_url}/{endpoint}"
        
        # === HTTPクライアントの作成 ===
        # async with: 非同期コンテキストマネージャー
        # 処理終了時に自動的にコネクションをクローズ
        async with httpx.AsyncClient() as client:
            
            # === リトライループ ===
            for attempt in range(retry_count):
                try:
                    # HTTPリクエストを送信
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        params=params,        # GET: ?key=value
                        json=json_data,       # POST/PUT: リクエストボディ
                        timeout=30.0          # 30秒でタイムアウト
                    )
                    
                    # === レート制限チェック ===
                    # Backlog APIは1時間あたりのリクエスト数に制限がある
                    if response.status_code == 429:  # Too Many Requests
                        # Retry-Afterヘッダーから待機時間を取得
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(
                            f"レート制限に達しました。{retry_after}秒待機します..."
                        )
                        await asyncio.sleep(retry_after)
                        continue  # 次の試行へ
                    
                    # ステータスコードが200番台以外なら例外を発生
                    response.raise_for_status()
                    
                    # JSONレスポンスをパース
                    return response.json()
                    
                except httpx.HTTPStatusError as e:
                    # HTTPエラー（4xx, 5xx）
                    logger.error(
                        f"HTTPエラー: {e.response.status_code} - "
                        f"{e.response.text}"
                    )
                    
                    # 最後の試行なら例外を再発生
                    if attempt == retry_count - 1:
                        raise
                    
                    # Exponential Backoff（指数関数的な待機）
                    # 1回目: 2^0 = 1秒
                    # 2回目: 2^1 = 2秒
                    # 3回目: 2^2 = 4秒
                    wait_time = 2 ** attempt
                    logger.info(f"リトライ {attempt + 1}/{retry_count} "
                              f"({wait_time}秒待機)")
                    await asyncio.sleep(wait_time)
                    
                except Exception as e:
                    # その他のエラー（ネットワークエラーなど）
                    logger.error(f"リクエストエラー: {str(e)}")
                    
                    if attempt == retry_count - 1:
                        raise
                    
                    await asyncio.sleep(2 ** attempt)
```

### 🔑 レート制限について

```python
"""
レート制限とは？
- APIの使用回数に制限をかける仕組み
- サーバーの過負荷を防ぐため

Backlog APIの制限：
- 1時間あたり1,000リクエスト（プランによる）
- 制限を超えると429エラー

対策：
1. Retry-Afterヘッダーの時間だけ待つ
2. リクエスト間隔を空ける
3. 必要最小限のリクエストにする
"""
```

### プロジェクト関連のメソッド

```python
    async def get_projects(self) -> List[Dict[str, Any]]:
        """全プロジェクトを取得"""
        return await self._make_request("GET", "projects")
    
    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """特定のプロジェクトを取得"""
        return await self._make_request("GET", f"projects/{project_id}")
    
    async def get_project_users(self, project_id: int) -> List[Dict[str, Any]]:
        """プロジェクトのユーザー一覧を取得"""
        return await self._make_request("GET", f"projects/{project_id}/users")
```

### タスク（課題）関連のメソッド

```python
    async def get_issues(
        self,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status_id: Optional[List[int]] = None,
        created_since: Optional[datetime] = None,
        updated_since: Optional[datetime] = None,
        count: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """課題一覧を取得"""
        
        params = {
            "count": count,
            "offset": offset
        }
        
        if project_id:
            params["projectId[]"] = project_id
        if assignee_id:
            params["assigneeId[]"] = assignee_id
        if status_id:
            params["statusId[]"] = status_id
        if created_since:
            params["createdSince"] = created_since.strftime("%Y-%m-%d")
        if updated_since:
            params["updatedSince"] = updated_since.strftime("%Y-%m-%d")
        
        return await self._make_request("GET", "issues", params=params)
    
    async def get_issue(self, issue_id: int) -> Dict[str, Any]:
        """特定の課題を取得"""
        return await self._make_request("GET", f"issues/{issue_id}")
    
    async def get_issue_comments(self, issue_id: int) -> List[Dict[str, Any]]:
        """課題のコメント一覧を取得"""
        return await self._make_request("GET", f"issues/{issue_id}/comments")
```

## 🔄 データ同期サービス

### 📊 なぜデータ同期が必要？

```
Backlog（元データ）         Team Insight（コピー）
┌──────────────┐          ┌──────────────┐
│ プロジェクト  │   同期→   │ プロジェクト  │
│ タスク       │          │ タスク       │
│ ユーザー      │          │ ユーザー      │
└──────────────┘          └──────────────┘

メリット：
1. 高速なデータアクセス（ローカルDB）
2. Backlog APIの負荷軽減
3. 独自の分析・集計が可能
4. オフライン時でもデータ参照可能
```

### 🔄 同期戦略

| 戦略 | 説明 | 使用場面 |
|------|------|----------|
| **全同期** | すべてのデータを取得 | 初回同期、日次バッチ |
| **差分同期** | 更新されたデータのみ | 定期的な更新 |
| **リアルタイム同期** | 変更を即座に反映 | Webhook使用時 |

### SyncServiceの実装

```python
# backend/app/services/sync_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models import User, Project, Task, ProjectMember, SyncHistory
from app.services.backlog_client import BacklogClient
from app.core.logging_config import get_logger
import asyncio

logger = get_logger(__name__)

class SyncService:
    """
    Backlogデータ同期サービス
    
    責務：
    - Backlogからデータを取得
    - ローカルDBに保存・更新
    - 同期履歴の管理
    - エラーハンドリング
    """
    
    def __init__(self, db: Session, backlog_client: BacklogClient):
        """
        Args:
            db: データベースセッション
            backlog_client: Backlog APIクライアント
        """
        self.db = db
        self.client = backlog_client
        
    async def sync_all_projects(self, user_id: str) -> Dict[str, Any]:
        """
        全プロジェクトを同期
        
        処理の流れ：
        1. 同期履歴レコードを作成（追跡用）
        2. Backlogから全プロジェクトを取得
        3. 各プロジェクトを個別に同期
        4. 結果を記録して返す
        """
        
        # === STEP 1: 同期履歴の作成 ===
        # 同期の開始を記録（監査・デバッグ用）
        sync_history = SyncHistory(
            user_id=user_id,
            sync_type="projects",      # 同期タイプ
            status="in_progress",      # 実行中
            started_at=datetime.utcnow()
        )
        self.db.add(sync_history)
        self.db.commit()  # 即座にコミット（進行状況を記録）
        
        try:
            # === STEP 2: Backlogからデータ取得 ===
            logger.info(f"プロジェクト同期開始: user_id={user_id}")
            backlog_projects = await self.client.get_projects()
            logger.info(f"取得したプロジェクト数: {len(backlog_projects)}")
            
            # カウンター初期化
            synced_count = 0  # 成功数
            error_count = 0   # 失敗数
            
            # === STEP 3: 個別同期 ===
            for bp in backlog_projects:
                try:
                    # 1プロジェクトずつ同期
                    await self._sync_single_project(bp)
                    synced_count += 1
                    
                    # 進捗ログ（10件ごと）
                    if synced_count % 10 == 0:
                        logger.info(f"同期進捗: {synced_count}/{len(backlog_projects)}")
                    
                except Exception as e:
                    # エラーが発生しても続行（1つの失敗で全体を止めない）
                    error_count += 1
                    logger.error(
                        f"プロジェクト同期エラー: "
                        f"project_id={bp['id']}, "
                        f"name={bp.get('name', 'Unknown')}, "
                        f"error={str(e)}"
                    )
            
            # === STEP 4: 同期履歴を更新 ===
            sync_history.status = "completed"
            sync_history.completed_at = datetime.utcnow()
            sync_history.items_synced = synced_count
            sync_history.items_failed = error_count
            
            # 実行時間を計算
            duration = (sync_history.completed_at - sync_history.started_at).total_seconds()
            logger.info(
                f"プロジェクト同期完了: "
                f"成功={synced_count}, "
                f"失敗={error_count}, "
                f"時間={duration:.2f}秒"
            )
            
            self.db.commit()
            
            # 結果を返す
            return {
                "synced": synced_count,
                "failed": error_count,
                "total": len(backlog_projects),
                "duration_seconds": duration
            }
            
        except Exception as e:
            # === エラー時の処理 ===
            logger.error(f"プロジェクト同期で致命的エラー: {str(e)}")
            
            # 同期履歴を失敗として記録
            sync_history.status = "failed"
            sync_history.error_message = str(e)
            sync_history.completed_at = datetime.utcnow()
            self.db.commit()
            
            # 例外を再発生（呼び出し元に通知）
            raise
    
    async def _sync_single_project(self, backlog_project: Dict[str, Any]) -> Project:
        """単一プロジェクトを同期"""
        
        # 既存プロジェクトを検索
        project = self.db.query(Project).filter(
            Project.backlog_project_id == backlog_project["id"]
        ).first()
        
        if project:
            # 更新
            project.name = backlog_project["name"]
            project.project_key = backlog_project["projectKey"]
            project.description = backlog_project.get("description")
            project.is_active = not backlog_project.get("archived", False)
            project.updated_at = datetime.utcnow()
        else:
            # 新規作成
            project = Project(
                backlog_project_id=backlog_project["id"],
                project_key=backlog_project["projectKey"],
                name=backlog_project["name"],
                description=backlog_project.get("description"),
                is_active=not backlog_project.get("archived", False)
            )
            self.db.add(project)
        
        self.db.flush()
        
        # プロジェクトメンバーも同期
        await self._sync_project_members(project.id, backlog_project["id"])
        
        return project
```

### タスク同期の実装

```python
    async def sync_project_tasks(
        self,
        project_id: str,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """プロジェクトのタスクを同期"""
        
        # プロジェクトを取得
        project = self.db.query(Project).filter(
            Project.id == project_id
        ).first()
        
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # 最終同期日時を決定
        if not since:
            # 前回の同期履歴から取得
            last_sync = self.db.query(SyncHistory).filter(
                SyncHistory.sync_type == "tasks",
                SyncHistory.project_id == project_id,
                SyncHistory.status == "completed"
            ).order_by(SyncHistory.completed_at.desc()).first()
            
            since = last_sync.completed_at if last_sync else datetime.utcnow() - timedelta(days=30)
        
        # Backlogからタスクを取得（ページング対応）
        all_tasks = []
        offset = 0
        count = 100
        
        while True:
            tasks = await self.client.get_issues(
                project_id=project.backlog_project_id,
                updated_since=since,
                count=count,
                offset=offset
            )
            
            if not tasks:
                break
                
            all_tasks.extend(tasks)
            offset += count
            
            # レート制限対策
            await asyncio.sleep(0.5)
        
        # タスクを同期
        synced_count = 0
        for task_data in all_tasks:
            try:
                await self._sync_single_task(task_data, project.id)
                synced_count += 1
            except Exception as e:
                logger.error(f"Failed to sync task {task_data['id']}: {str(e)}")
        
        self.db.commit()
        
        return {
            "project_id": project_id,
            "synced_tasks": synced_count,
            "total_tasks": len(all_tasks)
        }
    
    async def _sync_single_task(self, task_data: Dict[str, Any], project_id: str) -> Task:
        """単一タスクを同期"""
        
        # 既存タスクを検索
        task = self.db.query(Task).filter(
            Task.backlog_issue_id == task_data["id"]
        ).first()
        
        # 担当者の解決
        assignee_id = None
        if task_data.get("assignee"):
            assignee = self.db.query(User).filter(
                User.backlog_id == str(task_data["assignee"]["id"])
            ).first()
            if assignee:
                assignee_id = assignee.id
        
        # 作成者の解決
        created_by_id = None
        if task_data.get("createdUser"):
            creator = self.db.query(User).filter(
                User.backlog_id == str(task_data["createdUser"]["id"])
            ).first()
            if creator:
                created_by_id = creator.id
        
        if task:
            # 更新
            task.summary = task_data["summary"]
            task.description = task_data.get("description", "")
            task.status = task_data["status"]["name"]
            task.priority = task_data["priority"]["name"] if task_data.get("priority") else None
            task.assignee_id = assignee_id
            task.estimated_hours = task_data.get("estimatedHours")
            task.actual_hours = task_data.get("actualHours")
            task.start_date = self._parse_date(task_data.get("startDate"))
            task.due_date = self._parse_date(task_data.get("dueDate"))
            task.updated_at = self._parse_date(task_data["updated"])
            
            # 完了日の設定
            if task.status in ["完了", "Closed", "Done"]:
                task.completed_date = self._parse_date(task_data["updated"])
        else:
            # 新規作成
            task = Task(
                project_id=project_id,
                backlog_issue_id=task_data["id"],
                issue_key=task_data["issueKey"],
                summary=task_data["summary"],
                description=task_data.get("description", ""),
                status=task_data["status"]["name"],
                priority=task_data["priority"]["name"] if task_data.get("priority") else None,
                assignee_id=assignee_id,
                created_by_id=created_by_id,
                estimated_hours=task_data.get("estimatedHours"),
                actual_hours=task_data.get("actualHours"),
                start_date=self._parse_date(task_data.get("startDate")),
                due_date=self._parse_date(task_data.get("dueDate")),
                created_at=self._parse_date(task_data["created"]),
                updated_at=self._parse_date(task_data["updated"])
            )
            self.db.add(task)
        
        self.db.flush()
        return task
    
    def _parse_date(self, date_string: Optional[str]) -> Optional[datetime]:
        """Backlogの日付文字列をdatetimeに変換"""
        if not date_string:
            return None
        
        try:
            # Backlogの日付形式: "2024-01-15T10:30:00Z"
            return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        except:
            return None

## 📅 定期同期スケジューラー

### ⏰ なぜスケジューラーが必要？

```
手動同期の問題点：
- 誰かが忘れる可能性
- 夜間・休日の更新を反映できない
- 一定間隔での実行が困難

スケジューラーのメリット：
✅ 自動実行（24時間365日）
✅ 負荷の少ない時間帯に実行
✅ 失敗時の自動リトライ
✅ 実行履歴の記録
```

### 📊 同期スケジュール戦略

| データ種別 | 頻度 | 理由 |
|-----------|------|------|
| ユーザー情報 | 日次（深夜） | 変更頻度が低い |
| プロジェクト | 6時間ごと | 適度な鮮度を保つ |
| タスク | 12時間ごと | 更新頻度とAPI負荷のバランス |
| トークン更新 | 1時間ごと | 有効期限切れを防ぐ |

### APSchedulerの設定

```python
# backend/app/schedulers/sync_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.db.session import SessionLocal
from app.services.sync_service import SyncService
from app.services.backlog_client import BacklogClient
from app.models import User, OAuthToken
from app.core.logging_config import get_logger
import asyncio
from datetime import datetime, timedelta

logger = get_logger(__name__)

class SyncScheduler:
    """
    データ同期スケジューラー
    
    APScheduler（Advanced Python Scheduler）を使用
    非同期処理に対応したジョブスケジューリング
    """
    
    def __init__(self):
        # 非同期対応のスケジューラーを作成
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """
        定期実行ジョブを設定
        
        トリガーの種類：
        - CronTrigger: 特定の時刻に実行（cron形式）
        - IntervalTrigger: 一定間隔で実行
        - DateTrigger: 特定の日時に1回実行
        """
        
        # === ユーザー同期: 毎日午前2時 ===
        self.scheduler.add_job(
            self._sync_all_users,              # 実行する関数
            CronTrigger(hour=2, minute=0),     # 毎日2:00
            id="sync_users_daily",             # ジョブID（一意）
            name="Daily user sync",            # 表示名
            misfire_grace_time=3600,           # 遅延許容時間（1時間）
            max_instances=1,                   # 同時実行を防ぐ
            replace_existing=True              # 既存ジョブを置換
        )
        
        # misfire_grace_timeとは？
        # サーバー停止などで実行時刻を過ぎた場合、
        # この時間内なら遅れて実行する
        
        # === プロジェクト同期: 6時間ごと ===
        self.scheduler.add_job(
            self._sync_all_projects,
            IntervalTrigger(
                hours=6,                       # 6時間間隔
                start_date=datetime.now()      # 即座に開始
            ),
            id="sync_projects",
            name="Project sync every 6 hours",
            max_instances=1
        )
        
        # === アクティブプロジェクトのタスク同期: 12時間ごと ===
        self.scheduler.add_job(
            self._sync_active_project_tasks,
            IntervalTrigger(
                hours=12,
                jitter=300  # 実行時刻を最大5分ずらす（負荷分散）
            ),
            id="sync_active_tasks",
            name="Active project tasks sync",
            max_instances=1
        )
        
        # jitterとは？
        # 複数のサーバーで同時実行を避けるため、
        # ランダムに実行時刻をずらす機能
        
        # === トークンリフレッシュ: 1時間ごと ===
        self.scheduler.add_job(
            self._refresh_expiring_tokens,
            IntervalTrigger(hours=1),
            id="refresh_tokens",
            name="Refresh expiring OAuth tokens",
            max_instances=1
        )
    
    async def _sync_all_users(self):
        """全ユーザーの情報を同期"""
        logger.info("Starting scheduled user sync...")
        
        db = SessionLocal()
        try:
            # 管理者ユーザーのトークンを使用
            admin_token = db.query(OAuthToken).join(User).filter(
                User.is_active == True,
                OAuthToken.expires_at > datetime.utcnow()
            ).first()
            
            if not admin_token:
                logger.warning("No valid admin token found for user sync")
                return
            
            client = BacklogClient(admin_token.access_token)
            
            # 全ユーザーを取得
            backlog_users = await client.get_users()
            
            for user_data in backlog_users:
                existing_user = db.query(User).filter(
                    User.backlog_id == str(user_data["id"])
                ).first()
                
                if existing_user:
                    existing_user.name = user_data["name"]
                    existing_user.email = user_data["mailAddress"]
                else:
                    new_user = User(
                        backlog_id=str(user_data["id"]),
                        name=user_data["name"],
                        email=user_data["mailAddress"],
                        is_active=True
                    )
                    db.add(new_user)
            
            db.commit()
            logger.info(f"User sync completed. Synced {len(backlog_users)} users")
            
        except Exception as e:
            logger.error(f"User sync failed: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def _sync_active_project_tasks(self):
        """アクティブなプロジェクトのタスクを同期"""
        logger.info("Starting scheduled task sync for active projects...")
        
        db = SessionLocal()
        try:
            # アクティブなプロジェクトを取得
            active_projects = db.query(Project).filter(
                Project.is_active == True
            ).all()
            
            for project in active_projects:
                try:
                    # プロジェクトオーナーのトークンを取得
                    token = db.query(OAuthToken).join(User).join(ProjectMember).filter(
                        ProjectMember.project_id == project.id,
                        ProjectMember.role.in_(["LEADER", "ADMIN"]),
                        OAuthToken.expires_at > datetime.utcnow()
                    ).first()
                    
                    if not token:
                        logger.warning(f"No valid token for project {project.name}")
                        continue
                    
                    client = BacklogClient(token.access_token)
                    sync_service = SyncService(db, client)
                    
                    # 過去24時間の更新を同期
                    since = datetime.utcnow() - timedelta(hours=24)
                    result = await sync_service.sync_project_tasks(project.id, since)
                    
                    logger.info(f"Synced tasks for project {project.name}: {result}")
                    
                except Exception as e:
                    logger.error(f"Failed to sync tasks for project {project.name}: {str(e)}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Task sync failed: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    def start(self):
        """スケジューラーを開始"""
        self.scheduler.start()
        logger.info("Sync scheduler started")
    
    def stop(self):
        """スケジューラーを停止"""
        self.scheduler.shutdown()
        logger.info("Sync scheduler stopped")

# グローバルインスタンス
sync_scheduler = SyncScheduler()
```

## 🚨 エラーハンドリングとリトライ

### カスタム例外クラス

```python
# backend/app/core/exceptions.py
class BacklogAPIError(Exception):
    """Backlog API関連のエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class RateLimitError(BacklogAPIError):
    """レート制限エラー"""
    def __init__(self, retry_after: int):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds")
        self.retry_after = retry_after

class AuthenticationError(BacklogAPIError):
    """認証エラー"""
    pass

class SyncError(Exception):
    """同期処理エラー"""
    pass
```

### 高度なリトライロジック

```python
# backend/app/utils/retry.py
import asyncio
from functools import wraps
from typing import Type, Tuple, Callable, Any
import random

def async_retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """非同期関数用のリトライデコレータ"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            delay = initial_delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    attempt += 1
                    
                    if attempt >= max_attempts:
                        logger.error(f"Max retry attempts reached for {func.__name__}")
                        raise
                    
                    # リトライ間隔を計算
                    if hasattr(e, 'retry_after'):
                        delay = e.retry_after
                    else:
                        delay = min(delay * exponential_base, max_delay)
                    
                    # ジッターを追加（同時リトライを避ける）
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s. Error: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
            
        return wrapper
    return decorator

# 使用例
@async_retry(
    exceptions=(BacklogAPIError, httpx.HTTPError),
    max_attempts=5,
    initial_delay=2.0
)
async def sync_with_retry(project_id: str):
    """リトライ機能付き同期処理"""
    # 同期処理の実装
    pass
```

## 🗄️ Redisキャッシュ統合

### キャッシュ戦略

```python
# backend/app/services/cache_service.py
import json
from typing import Optional, Any, Dict
from datetime import timedelta
from app.core.redis_client import redis_client
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class CacheService:
    """Redisキャッシュサービス"""
    
    # キャッシュキーのプレフィックス
    PREFIXES = {
        "project": "project:",
        "task": "task:",
        "user": "user:",
        "dashboard": "dashboard:",
        "sync": "sync:"
    }
    
    # デフォルトの有効期限
    DEFAULT_EXPIRY = {
        "project": timedelta(hours=6),
        "task": timedelta(hours=1),
        "user": timedelta(hours=24),
        "dashboard": timedelta(minutes=15),
        "sync": timedelta(minutes=5)
    }
    
    @classmethod
    async def get(cls, key_type: str, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        redis_key = cls.PREFIXES[key_type] + key
        
        try:
            redis_conn = await redis_client.get_connection()
            cached = await redis_conn.get(redis_key)
            
            if cached:
                logger.debug(f"Cache hit: {redis_key}")
                return json.loads(cached)
            
            logger.debug(f"Cache miss: {redis_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    @classmethod
    async def set(
        cls,
        key_type: str,
        key: str,
        value: Any,
        expiry: Optional[timedelta] = None
    ) -> bool:
        """キャッシュに値を設定"""
        redis_key = cls.PREFIXES[key_type] + key
        
        if expiry is None:
            expiry = cls.DEFAULT_EXPIRY[key_type]
        
        try:
            redis_conn = await redis_client.get_connection()
            await redis_conn.setex(
                redis_key,
                int(expiry.total_seconds()),
                json.dumps(value, ensure_ascii=False, default=str)
            )
            
            logger.debug(f"Cache set: {redis_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    @classmethod
    async def delete(cls, key_type: str, key: str) -> bool:
        """キャッシュから削除"""
        redis_key = cls.PREFIXES[key_type] + key
        
        try:
            redis_conn = await redis_client.get_connection()
            await redis_conn.delete(redis_key)
            logger.debug(f"Cache deleted: {redis_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    @classmethod
    async def invalidate_pattern(cls, pattern: str) -> int:
        """パターンに一致するキーを無効化"""
        try:
            redis_conn = await redis_client.get_connection()
            
            # パターンに一致するキーを検索
            keys = []
            async for key in redis_conn.scan_iter(match=pattern):
                keys.append(key)
            
            # 一括削除
            if keys:
                deleted = await redis_conn.delete(*keys)
                logger.info(f"Invalidated {deleted} cache keys matching {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return 0
```

### キャッシュ付きサービス

```python
# backend/app/services/cached_project_service.py
from app.services.project_service import ProjectService
from app.services.cache_service import CacheService
from typing import List, Optional
from app.schemas.project import ProjectResponse

class CachedProjectService(ProjectService):
    """キャッシュ機能付きプロジェクトサービス"""
    
    async def get_user_projects(self, user_id: str) -> List[ProjectResponse]:
        """ユーザーのプロジェクト一覧を取得（キャッシュ付き）"""
        
        # キャッシュチェック
        cache_key = f"user_projects:{user_id}"
        cached = await CacheService.get("project", cache_key)
        
        if cached:
            return [ProjectResponse(**p) for p in cached]
        
        # DBから取得
        projects = super().get_user_projects(user_id)
        
        # キャッシュに保存
        await CacheService.set(
            "project",
            cache_key,
            [p.dict() for p in projects]
        )
        
        return projects
    
    async def update_project(self, project_id: str, data: dict) -> ProjectResponse:
        """プロジェクトを更新（キャッシュ無効化付き）"""
        
        # プロジェクトを更新
        project = super().update_project(project_id, data)
        
        # 関連キャッシュを無効化
        await CacheService.delete("project", f"detail:{project_id}")
        await CacheService.invalidate_pattern(f"project:user_projects:*")
        
        return project
```

## 🎯 フロントエンドでのAPI呼び出し

### APIサービスの実装

```typescript
// frontend/src/services/syncService.ts
import apiClient from '@/lib/api-client'
import { SyncStatus, SyncHistory, SyncResult } from '@/types/sync'

export const syncService = {
  // 接続状態を確認
  async getConnectionStatus(): Promise<SyncStatus> {
    const response = await apiClient.get('/api/v1/sync/connection/status')
    return response.data
  },

  // 全プロジェクトを同期
  async syncAllProjects(): Promise<SyncResult> {
    const response = await apiClient.post('/api/v1/sync/projects/all')
    return response.data
  },

  // 特定プロジェクトのタスクを同期
  async syncProjectTasks(projectId: string): Promise<SyncResult> {
    const response = await apiClient.post(
      `/api/v1/sync/project/${projectId}/tasks`
    )
    return response.data
  },

  // 同期履歴を取得
  async getSyncHistory(params?: {
    syncType?: string
    projectId?: string
    limit?: number
  }): Promise<SyncHistory[]> {
    const response = await apiClient.get('/api/v1/sync/history', { params })
    return response.data
  },
}
```

### React Queryフックの実装

```tsx
// frontend/src/hooks/queries/useSync.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { syncService } from '@/services/syncService'
import { toast } from '@/components/ui/use-toast'

// 接続状態の監視
export const useConnectionStatus = () => {
  return useQuery({
    queryKey: ['sync', 'connection'],
    queryFn: syncService.getConnectionStatus,
    refetchInterval: 30000, // 30秒ごとに確認
    staleTime: 20000,
  })
}

// プロジェクト同期
export const useSyncAllProjects = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: syncService.syncAllProjects,
    onSuccess: (data) => {
      // 関連するクエリを無効化
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['sync', 'history'] })
      
      toast({
        title: '同期完了',
        description: `${data.synced}件のプロジェクトを同期しました`,
      })
    },
    onError: (error: any) => {
      toast({
        title: '同期エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

// タスク同期
export const useSyncProjectTasks = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (projectId: string) => syncService.syncProjectTasks(projectId),
    onSuccess: (data, projectId) => {
      // タスク一覧を更新
      queryClient.invalidateQueries({ 
        queryKey: ['tasks', { projectId }] 
      })
      
      toast({
        title: 'タスク同期完了',
        description: `${data.synced_tasks}件のタスクを同期しました`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'タスク同期エラー',
        description: error.response?.data?.detail || '同期に失敗しました',
        variant: 'destructive',
      })
    },
  })
}

// 同期履歴
export const useSyncHistory = (params?: {
  syncType?: string
  projectId?: string
}) => {
  return useQuery({
    queryKey: ['sync', 'history', params],
    queryFn: () => syncService.getSyncHistory(params),
    staleTime: 60000, // 1分
  })
}
```

### 同期UIコンポーネント

```tsx
// frontend/src/components/sync/SyncButton.tsx
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import { useSyncAllProjects } from '@/hooks/queries/useSync'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

export function SyncButton() {
  const [showConfirm, setShowConfirm] = useState(false)
  const syncMutation = useSyncAllProjects()

  const handleSync = () => {
    setShowConfirm(false)
    syncMutation.mutate()
  }

  return (
    <>
      <Button
        onClick={() => setShowConfirm(true)}
        disabled={syncMutation.isPending}
        variant="outline"
      >
        <RefreshCw 
          className={`mr-2 h-4 w-4 ${
            syncMutation.isPending ? 'animate-spin' : ''
          }`} 
        />
        {syncMutation.isPending ? '同期中...' : 'Backlogと同期'}
      </Button>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>データ同期の確認</AlertDialogTitle>
            <AlertDialogDescription>
              Backlogから最新のデータを取得します。
              プロジェクト数によっては時間がかかる場合があります。
              続行しますか？
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>キャンセル</AlertDialogCancel>
            <AlertDialogAction onClick={handleSync}>
              同期開始
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
```

### 同期状態の表示

```tsx
// frontend/src/components/sync/ConnectionStatus.tsx
'use client'

import { useConnectionStatus } from '@/hooks/queries/useSync'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'

export function ConnectionStatus() {
  const { data: status, isLoading } = useConnectionStatus()

  if (isLoading) {
    return (
      <Badge variant="secondary">
        <AlertCircle className="mr-1 h-3 w-3" />
        接続確認中...
      </Badge>
    )
  }

  if (!status?.connected) {
    return (
      <Badge variant="destructive">
        <XCircle className="mr-1 h-3 w-3" />
        Backlog未接続
      </Badge>
    )
  }

  return (
    <Badge variant="success">
      <CheckCircle className="mr-1 h-3 w-3" />
      {status.space_key}に接続中
    </Badge>
  )
}
```

## 🔍 デバッグとモニタリング

### APIリクエストのロギング

```python
# backend/app/middleware/logging_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import json

class APILoggingMiddleware(BaseHTTPMiddleware):
    """APIリクエスト/レスポンスをログ出力"""
    
    async def dispatch(self, request: Request, call_next):
        # リクエスト情報を記録
        start_time = time.time()
        
        # リクエストボディを読み取り（必要に応じて）
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            # ボディを再度読めるようにする
            request._body = body
        
        # 同期APIの場合は詳細ログ
        if "/sync/" in str(request.url):
            logger.info(
                f"Sync API Request: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host,
                    "body": body.decode() if body else None
                }
            )
        
        # レスポンス処理
        response = await call_next(request)
        
        # 処理時間を計算
        process_time = time.time() - start_time
        
        # レスポンスログ
        if "/sync/" in str(request.url):
            logger.info(
                f"Sync API Response: {response.status_code} in {process_time:.3f}s",
                extra={
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "path": request.url.path
                }
            )
        
        # 遅いリクエストを警告
        if process_time > 5.0:
            logger.warning(
                f"Slow API request: {request.url.path} took {process_time:.3f}s"
            )
        
        return response
```

### 同期パフォーマンスの監視

```python
# backend/app/services/sync_monitor.py
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime, timedelta
import asyncio

@dataclass
class SyncMetrics:
    """同期メトリクス"""
    project_id: str
    sync_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    items_processed: int = 0
    items_failed: int = 0
    error_messages: List[str] = field(default_factory=list)

class SyncMonitor:
    """同期処理の監視"""
    
    def __init__(self):
        self.active_syncs: Dict[str, SyncMetrics] = {}
        self.completed_syncs: List[SyncMetrics] = []
        self._lock = asyncio.Lock()
    
    async def start_sync(self, sync_id: str, project_id: str, sync_type: str):
        """同期開始を記録"""
        async with self._lock:
            self.active_syncs[sync_id] = SyncMetrics(
                project_id=project_id,
                sync_type=sync_type,
                start_time=datetime.utcnow()
            )
    
    async def update_progress(self, sync_id: str, items_processed: int):
        """進捗を更新"""
        async with self._lock:
            if sync_id in self.active_syncs:
                self.active_syncs[sync_id].items_processed = items_processed
    
    async def complete_sync(self, sync_id: str, items_failed: int = 0):
        """同期完了を記録"""
        async with self._lock:
            if sync_id in self.active_syncs:
                metrics = self.active_syncs.pop(sync_id)
                metrics.end_time = datetime.utcnow()
                metrics.items_failed = items_failed
                self.completed_syncs.append(metrics)
                
                # メトリクスをログ出力
                duration = (metrics.end_time - metrics.start_time).total_seconds()
                logger.info(
                    f"Sync completed: {metrics.sync_type} for project {metrics.project_id}",
                    extra={
                        "duration": duration,
                        "items_processed": metrics.items_processed,
                        "items_failed": metrics.items_failed,
                        "items_per_second": metrics.items_processed / duration if duration > 0 else 0
                    }
                )
    
    async def get_active_syncs(self) -> List[Dict]:
        """アクティブな同期のリストを取得"""
        async with self._lock:
            return [
                {
                    "sync_id": sync_id,
                    "project_id": m.project_id,
                    "sync_type": m.sync_type,
                    "duration": (datetime.utcnow() - m.start_time).total_seconds(),
                    "items_processed": m.items_processed
                }
                for sync_id, m in self.active_syncs.items()
            ]
    
    async def get_sync_stats(self, hours: int = 24) -> Dict:
        """同期統計を取得"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        recent_syncs = [
            s for s in self.completed_syncs 
            if s.start_time > since
        ]
        
        if not recent_syncs:
            return {
                "total_syncs": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "total_items": 0
            }
        
        total_duration = sum(
            (s.end_time - s.start_time).total_seconds() 
            for s in recent_syncs
        )
        
        total_items = sum(s.items_processed for s in recent_syncs)
        failed_syncs = sum(1 for s in recent_syncs if s.items_failed > 0)
        
        return {
            "total_syncs": len(recent_syncs),
            "success_rate": (len(recent_syncs) - failed_syncs) / len(recent_syncs) * 100,
            "avg_duration": total_duration / len(recent_syncs),
            "total_items": total_items,
            "items_per_hour": total_items / (hours if hours > 0 else 1)
        }

# グローバルインスタンス
sync_monitor = SyncMonitor()
```

### フロントエンドでの同期監視

```tsx
// frontend/src/components/sync/SyncMonitor.tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Activity, Clock, CheckCircle, XCircle } from 'lucide-react'

export function SyncMonitor() {
  const { data: activesyncs } = useQuery({
    queryKey: ['sync', 'active'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/sync/monitor/active')
      return response.data
    },
    refetchInterval: 2000, // 2秒ごとに更新
  })

  const { data: stats } = useQuery({
    queryKey: ['sync', 'stats'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/sync/monitor/stats')
      return response.data
    },
    refetchInterval: 60000, // 1分ごとに更新
  })

  return (
    <div className="space-y-4">
      {/* アクティブな同期 */}
      {activesyncs && activesyncs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 animate-pulse" />
              同期実行中
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {activesyncs.map((sync: any) => (
              <div key={sync.sync_id} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{sync.sync_type}</span>
                  <span>{sync.items_processed}件処理</span>
                </div>
                <Progress value={sync.progress || 0} />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 同期統計 */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle>過去24時間の同期統計</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">実行回数</p>
                <p className="text-2xl font-bold">{stats.total_syncs}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">成功率</p>
                <p className="text-2xl font-bold">{stats.success_rate.toFixed(1)}%</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">平均時間</p>
                <p className="text-2xl font-bold">{stats.avg_duration.toFixed(1)}秒</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">処理アイテム</p>
                <p className="text-2xl font-bold">{stats.total_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
```

## 💡 開発のベストプラクティス

1. **API呼び出しの最適化**
   - バッチ処理でAPI呼び出し回数を削減
   - 適切なページサイズの設定
   - 並列処理の活用

2. **エラー処理**
   - リトライ可能なエラーとそうでないエラーを区別
   - ユーザーフレンドリーなエラーメッセージ
   - エラーログの詳細記録

3. **キャッシュ戦略**
   - 頻繁に変更されないデータは長めにキャッシュ
   - 同期後は関連キャッシュを無効化
   - キャッシュミスに備えた実装

4. **監視とアラート**
   - 同期処理の実行時間を監視
   - 失敗率の追跡
   - 異常な処理時間の検出

---

次は[テスト戦略とTDD](08-testing.md)で、品質の高いコードを書く方法を学びましょう！
```