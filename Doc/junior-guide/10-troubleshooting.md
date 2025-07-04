# トラブルシューティング

**このガイドで学べること**：
- よくあるエラーと解決方法
- デバッグ手法とツール
- パフォーマンス問題の診断
- ログ分析のテクニック

## 🚨 よくあるエラーと解決方法

### 1. Docker関連のエラー

#### ポート競合エラー
```
Error: bind: address already in use
```

**原因**: 他のアプリケーションが同じポートを使用している

**解決方法**:
```bash
# 使用中のポートを確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド
lsof -i :5432  # PostgreSQL

# プロセスを停止
kill -9 <PID>

# または、docker-compose.ymlでポートを変更
ports:
  - "3001:3000"  # 3001に変更
```

#### コンテナが起動しない
```
container_name exited with code 1
```

**デバッグ手順**:
```bash
# ログを確認
docker-compose logs backend
docker-compose logs frontend

# コンテナに入って確認
docker-compose run --rm backend bash
```

### 2. データベース関連のエラー

#### 接続エラー
```
psycopg2.OperationalError: could not connect to server
```

**原因と解決**:
1. PostgreSQLが起動していない
   ```bash
   docker-compose ps postgres
   docker-compose up -d postgres
   ```

2. 接続情報が間違っている
   ```bash
   # .envファイルを確認
   DATABASE_URL=postgresql://teaminsight:teaminsight@postgres:5432/teaminsight
   ```

3. ネットワークの問題
   ```bash
   # コンテナ間の通信を確認
   docker-compose exec backend ping postgres
   ```

#### マイグレーションエラー
```
alembic.util.exc.CommandError: Can't locate revision identifier
```

**解決方法**:
```bash
# 現在のリビジョンを確認
docker-compose exec backend alembic current

# 履歴を確認
docker-compose exec backend alembic history

# 強制的に最新に更新（注意：データ損失の可能性）
docker-compose exec backend alembic stamp head
```

### 3. 認証関連のエラー

#### JWTトークンエラー
```
401 Unauthorized: Invalid token
```

**デバッグ**:
```python
# backend/app/api/deps.py にデバッグログを追加
import logging
logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Token payload: {payload}")
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
```

#### Backlog OAuth エラー
```
space_not_allowed: User is not member of specified space
```

**確認事項**:
1. BACKLOG_SPACE_KEYが正しいか
2. ユーザーがそのスペースのメンバーか
3. OAuth アプリの設定が正しいか

### 4. フロントエンド関連のエラー

#### ビルドエラー
```
Module not found: Can't resolve '@/components/...'
```

**解決方法**:
```bash
# 依存関係を再インストール
cd frontend
rm -rf node_modules .yarn/cache
yarn install

# TypeScript設定を確認
cat tsconfig.json | grep -A 5 "paths"
```

#### ハイドレーションエラー
```
Error: Hydration failed because the initial UI does not match
```

**原因**: サーバーとクライアントでレンダリング結果が異なる

**解決方法**:
```tsx
// 条件付きレンダリングにuseEffectを使用
const [mounted, setMounted] = useState(false)

useEffect(() => {
  setMounted(true)
}, [])

if (!mounted) return null
```

### 5. API関連のエラー

#### CORS エラー
```
Access to XMLHttpRequest blocked by CORS policy
```

**バックエンドの設定確認**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### タイムアウトエラー
```
Request timeout after 30000ms
```

**解決方法**:
1. Nginxのタイムアウト設定を確認
2. バックエンドの処理を最適化
3. 大量データの場合はページネーションを使用

## 🔍 デバッグ手法

### バックエンドのデバッグ

#### 1. インタラクティブデバッグ

```python
# pdbを使用したデバッグ
import pdb

@router.get("/debug")
async def debug_endpoint():
    pdb.set_trace()  # ここでブレークポイント
    result = some_function()
    return result

# IPythonを使用（より高機能）
from IPython import embed

def complex_function():
    data = get_data()
    embed()  # ここでIPythonシェルが起動
    process_data(data)
```

#### 2. SQLクエリのデバッグ

```python
# SQLAlchemyのクエリログを有効化
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 実際のSQLを確認
from sqlalchemy.dialects import postgresql

query = db.query(User).filter(User.email == "test@example.com")
print(query.statement.compile(dialect=postgresql.dialect()))
```

#### 3. APIリクエストのデバッグ

```python
# リクエスト/レスポンスのロギング
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    # ボディを読む（注意：一度しか読めない）
    body = await request.body()
    logger.debug(f"Body: {body.decode()}")
    
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

### フロントエンドのデバッグ

#### 1. React Developer Tools

```javascript
// コンポーネントの状態を確認
if (process.env.NODE_ENV === 'development') {
  window.__REACT_DEVTOOLS_GLOBAL_HOOK__.onCommitFiberRoot = (id, root) => {
    console.log('Component tree updated', root)
  }
}
```

#### 2. Redux DevTools

```typescript
// store設定でDevToolsを有効化
export const store = configureStore({
  reducer: rootReducer,
  devTools: process.env.NODE_ENV === 'development',
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(logger),
})
```

#### 3. ネットワークデバッグ

```typescript
// APIクライアントにインターセプターを追加
apiClient.interceptors.request.use((config) => {
  console.group(`🚀 ${config.method?.toUpperCase()} ${config.url}`)
  console.log('Headers:', config.headers)
  console.log('Data:', config.data)
  console.groupEnd()
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    console.group(`✅ ${response.config.url}`)
    console.log('Status:', response.status)
    console.log('Data:', response.data)
    console.groupEnd()
    return response
  },
  (error) => {
    console.group(`❌ ${error.config?.url}`)
    console.error('Error:', error.response?.data || error.message)
    console.groupEnd()
    return Promise.reject(error)
  }
)
```

### Dockerコンテナのデバッグ

#### 1. コンテナ内部の調査

```bash
# 実行中のプロセスを確認
docker-compose exec backend ps aux

# ファイルシステムを確認
docker-compose exec backend ls -la /app

# 環境変数を確認
docker-compose exec backend env | grep -E "(DATABASE|REDIS|SECRET)"

# パッケージのバージョンを確認
docker-compose exec backend pip list
```

#### 2. ログの詳細分析

```bash
# タイムスタンプ付きでログを表示
docker-compose logs -t backend

# 特定の時間範囲のログ
docker-compose logs --since 2024-01-01T10:00:00 --until 2024-01-01T11:00:00

# エラーのみフィルタリング
docker-compose logs backend 2>&1 | grep -E "(ERROR|CRITICAL|Exception)"
```

## ⚡ パフォーマンス問題の診断

### データベースの遅延

#### 1. スロークエリの特定

```sql
-- PostgreSQLでスロークエリを確認
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- 1秒以上
ORDER BY mean_time DESC
LIMIT 10;

-- 実行中のクエリを確認
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 minute';
```

#### 2. インデックスの最適化

```python
# N+1問題の解決
# ❌ 悪い例
users = db.query(User).all()
for user in users:
    tasks = db.query(Task).filter(Task.user_id == user.id).all()

# ✅ 良い例
users = db.query(User).options(joinedload(User.tasks)).all()
```

### APIレスポンスの遅延

#### 1. プロファイリング

```python
# cProfileを使用
import cProfile
import pstats

def profile_endpoint():
    pr = cProfile.Profile()
    pr.enable()
    
    # 処理
    result = expensive_operation()
    
    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 上位10個
    
    return result
```

#### 2. 非同期処理の活用

```python
# 並列実行で高速化
import asyncio

async def fetch_all_data(user_id: str):
    # 並列実行
    results = await asyncio.gather(
        get_user_projects(user_id),
        get_user_tasks(user_id),
        get_user_stats(user_id)
    )
    return results
```

### メモリリーク

#### 1. メモリ使用量の監視

```python
import psutil
import os

def get_memory_info():
    process = psutil.Process(os.getpid())
    return {
        "rss": process.memory_info().rss / 1024 / 1024,  # MB
        "vms": process.memory_info().vms / 1024 / 1024,  # MB
        "percent": process.memory_percent()
    }
```

#### 2. メモリプロファイリング

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # 大量のデータ処理
    large_list = [i for i in range(1000000)]
    return sum(large_list)
```

## 📝 トラブルシューティングチェックリスト

### 問題発生時の確認手順

1. **エラーメッセージの詳細確認**
   - スタックトレースの完全な内容
   - エラーが発生した時刻
   - リクエストIDやユーザー情報

2. **環境の確認**
   - Docker コンテナの状態
   - ディスク容量
   - メモリ使用量
   - CPU使用率

3. **ログの収集**
   ```bash
   # すべてのログを一括収集
   mkdir -p /tmp/team-insight-logs
   docker-compose logs > /tmp/team-insight-logs/docker.log
   docker-compose exec backend cat /app/logs/app.log > /tmp/team-insight-logs/app.log
   docker-compose exec postgres cat /var/log/postgresql/postgresql.log > /tmp/team-insight-logs/postgres.log
   ```

4. **再現手順の確認**
   - 問題が発生する具体的な操作
   - 特定のデータやユーザーで発生するか
   - 時間帯による影響はあるか

5. **一時的な対処**
   - サービスの再起動
   - キャッシュのクリア
   - 一時的な機能の無効化

## 🆘 緊急時の対応

### サービス完全停止時

```bash
# 1. 全サービスを安全に停止
docker-compose down

# 2. ボリュームを保持したまま再構築
docker-compose build --no-cache
docker-compose up -d

# 3. ヘルスチェック
curl http://localhost/health
```

### データベース破損時

```bash
# 1. バックアップからリストア
./scripts/restore.sh 20240101_120000

# 2. 整合性チェック
docker-compose exec postgres psql -U teaminsight -c "REINDEX DATABASE teaminsight;"
```

---

次は[コマンドリファレンス](appendix-commands.md)で、便利なコマンド一覧を確認しましょう！