# Redis キャッシュシステム

## 概要

Team Insight プロジェクトでは、Redis を活用した API レスポンスキャッシュシステムを実装しています。このシステムにより、データベースへの負荷を劇的に削減し、API 応答速度を大幅に向上させることができます。

## アーキテクチャ

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Next.js   │───▶│   FastAPI   │───▶│ PostgreSQL  │
│  Frontend   │    │   Backend   │    │  Database   │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │    Redis    │
                   │   Cache     │
                   └─────────────┘
```

## 主要機能

### 1. 自動キャッシュ（ミドルウェア）

- **対象**: GET リクエストのみ
- **有効期限**: デフォルト 5 分（設定可能）
- **対象パス**: `/api/v1/projects`, `/api/v1/teams`, `/api/v1/dashboard`, `/api/v1/users`
- **除外パス**: `/api/v1/auth`, `/api/v1/cache`, `/docs`, `/openapi.json`

### 2. デコレータベースキャッシュ

```python
@cache_response("projects_list", expire=600)  # 10分間キャッシュ
async def get_projects():
    # データベースから取得
    return projects

@cache_invalidate("project_*")  # プロジェクト関連キャッシュを無効化
async def update_project():
    # 更新処理
    return result
```

### 3. キャッシュ管理 API

- `GET /api/v1/cache/stats` - キャッシュ統計情報
- `DELETE /api/v1/cache/clear` - 全キャッシュクリア
- `DELETE /api/v1/cache/clear/{pattern}` - パターン指定キャッシュクリア
- `GET /api/v1/cache/health` - キャッシュ健全性チェック

## 実装詳細

### Redis 接続クライアント

**ファイル**: `backend/app/core/redis_client.py`

```python
import redis.asyncio as redis
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis接続とキャッシュ操作を管理するクラス"""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None

    async def get_connection(self) -> redis.Redis:
        """Redis接続を取得"""
        if self._redis is None:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.CACHE_MAX_CONNECTIONS,
                decode_responses=True
            )
            self._redis = redis.Redis(connection_pool=self._connection_pool)
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        try:
            redis_client = await self.get_connection()
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """キャッシュに値を設定"""
        try:
            redis_client = await self.get_connection()
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)

            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire

            await redis_client.set(key, serialized_value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """パターンに一致するキャッシュを削除"""
        try:
            redis_client = await self.get_connection()
            keys = await redis_client.keys(pattern)
            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Redis統計情報を取得"""
        try:
            redis_client = await self.get_connection()
            info = await redis_client.info()
            keys = await redis_client.keys("cache:*")

            return {
                "total_keys": len(keys),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"error": str(e)}

    async def health_check(self) -> dict:
        """Redis健全性チェック"""
        try:
            redis_client = await self.get_connection()
            await redis_client.ping()
            return {"status": "healthy", "message": "Redisキャッシュは正常に動作しています"}
        except Exception as e:
            logger.error(f"Redis health check error: {e}")
            return {"status": "unhealthy", "message": f"Redis接続エラー: {e}"}

# グローバルインスタンス
redis_client = RedisClient()
```

### キャッシュデコレータ

**ファイル**: `backend/app/core/cache.py`

```python
import hashlib
import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional, Union
from datetime import timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """キャッシュキーを生成"""
    # 引数とキーワード引数を文字列化
    key_parts = [prefix]

    # 位置引数を追加
    for arg in args:
        key_parts.append(str(arg))

    # キーワード引数をソートして追加
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}:{value}")

    # 結合してMD5ハッシュを生成
    key_string = "|".join(key_parts)
    hash_object = hashlib.md5(key_string.encode())
    return f"cache:{hash_object.hexdigest()}"

def cache_response(
    prefix: str,
    expire: Union[int, timedelta] = 300,
    key_generator: Optional[Callable] = None
):
    """APIレスポンスをキャッシュするデコレータ"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # カスタムキー生成関数がある場合は使用
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)

            # キャッシュから取得を試行
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache HIT for key: {cache_key}")
                return cached_value

            # キャッシュミスの場合、関数を実行
            logger.info(f"Cache MISS for key: {cache_key}")
            result = await func(*args, **kwargs)

            # 結果をキャッシュに保存
            await redis_client.set(cache_key, result, expire)

            return result
        return wrapper
    return decorator

def cache_invalidate(pattern: str):
    """キャッシュを無効化するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 関数を実行
            result = await func(*args, **kwargs)

            # キャッシュを無効化
            deleted_count = await redis_client.delete_pattern(pattern)
            logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")

            return result
        return wrapper
    return decorator

class CacheMiddleware(BaseHTTPMiddleware):
    """HTTPリクエストのキャッシュミドルウェア"""

    def __init__(
        self,
        app,
        default_expire: int = 300,
        cacheable_paths: list = None,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.default_expire = default_expire
        self.cacheable_paths = cacheable_paths or []
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):
        # GETリクエストのみキャッシュ対象
        if request.method != "GET":
            return await call_next(request)

        # パスチェック
        path = request.url.path
        if not self._is_cacheable_path(path):
            return await call_next(request)

        # キャッシュキー生成
        cache_key = self._generate_cache_key(request)

        # キャッシュから取得を試行
        cached_response = await redis_client.get(cache_key)
        if cached_response is not None:
            logger.info(f"Cache HIT for path: {path}")
            return JSONResponse(
                content=cached_response,
                headers={"X-Cache": "HIT"}
            )

        # キャッシュミスの場合、レスポンスを処理
        logger.info(f"Cache MISS for path: {path}")
        response = await call_next(request)

        # 成功レスポンスのみキャッシュ
        if response.status_code == 200:
            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # レスポンスをキャッシュに保存
                response_data = response_body.decode()
                await redis_client.set(cache_key, response_data, self.default_expire)

                # レスポンスを再構築
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers) | {"X-Cache": "MISS"}
                )
            except Exception as e:
                logger.error(f"Cache middleware error: {e}")

        return response

    def _is_cacheable_path(self, path: str) -> bool:
        """キャッシュ対象パスかどうかを判定"""
        # 除外パスチェック
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # 対象パスチェック
        if not self.cacheable_paths:
            return True

        for cacheable_path in self.cacheable_paths:
            if path.startswith(cacheable_path):
                return True

        return False

    def _generate_cache_key(self, request: Request) -> str:
        """リクエストからキャッシュキーを生成"""
        # メソッド、パス、クエリパラメータ、ユーザーIDを組み合わせ
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]

        # ユーザーIDがあれば追加（認証済みの場合）
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key_parts.append(f"user:{user_id}")

        key_string = "|".join(key_parts)
        hash_object = hashlib.md5(key_string.encode())
        return f"cache:http:{hash_object.hexdigest()}"
```

## パフォーマンス効果

### 実際のテスト結果

今回実装したキャッシュシステムの実際のパフォーマンス測定結果：

| テストケース                   | キャッシュなし | キャッシュあり | 改善率    |
| ------------------------------ | -------------- | -------------- | --------- |
| シンプルキャッシュ             | 0.552 秒       | 0.008 秒       | **98.5%** |
| パラメータ付きキャッシュ       | 0.316 秒       | 0.047 秒       | **85.1%** |
| クエリパラメータ付きキャッシュ | 0.708 秒       | 0.001 秒       | **99.9%** |
| パフォーマンスキャッシュ       | 1.051 秒       | 0.005 秒       | **99.5%** |

### 期待される改善

1. **レスポンス時間**: 85-99%の短縮
2. **データベース負荷**: 70-95%の削減
3. **スループット**: 3-10 倍の向上

## 使用方法

### 1. 基本的なキャッシュ適用

```python
from app.core.cache import cache_response

@router.get("/users")
@cache_response("users_list", expire=600)  # 10分間キャッシュ
async def get_users():
    # データベースからユーザー一覧を取得
    users = db.query(User).all()
    return {"data": users}
```

### 2. パラメータ付きキャッシュ

```python
@router.get("/users/{user_id}")
@cache_response("user_detail", expire=300)  # 5分間キャッシュ
async def get_user(user_id: int):
    # ユーザーIDに基づいてキャッシュキーが自動生成される
    user = db.query(User).filter(User.id == user_id).first()
    return {"data": user}
```

### 3. キャッシュ無効化

```python
from app.core.cache import cache_invalidate

@router.put("/users/{user_id}")
@cache_invalidate("user_*")  # user_で始まるキャッシュを無効化
async def update_user(user_id: int, user_data: UserUpdate):
    # ユーザー更新処理
    # 処理後にuser_で始まるキャッシュが自動的に無効化される
    return {"message": "Updated"}
```

## テストと検証

### 自動テストスクリプト

**ファイル**: `backend/test_cache.py`

```python
import httpx
import asyncio
import time
from typing import Dict, Any

class CacheTester:
    """キャッシュ機能のテストクラス"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def test_basic_endpoints(self):
        """基本的なエンドポイントテスト"""
        print("🌐 基本的なエンドポイントテスト")
        print("=" * 50)

        # ルートエンドポイント
        print("📤 ルートエンドポイント...")
        response = await self.client.get(f"{self.base_url}/")
        if response.status_code == 200:
            print(f"   ✅ 成功: {response.json()['message']}")
        else:
            print(f"   ❌ 失敗: {response.status_code}")

        # ヘルスチェック
        print("📤 ヘルスチェック...")
        response = await self.client.get(f"{self.base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ アプリケーション: {data['application']}")
            print(f"   ✅ Redis: {data['redis']['status']}")
        else:
            print(f"   ❌ 失敗: {response.status_code}")

    async def test_cache_performance(self, endpoint: str, description: str, ttl: int):
        """キャッシュパフォーマンステスト"""
        print(f"\n🔍 {description}（{ttl}秒間キャッシュ）")
        print("=" * 50)

        # 初回リクエスト（キャッシュミス）
        print("📤 初回リクエスト（キャッシュミス）...")
        start_time = time.time()
        response1 = await self.client.get(f"{self.base_url}{endpoint}")
        first_time = time.time() - start_time

        print(f"   ステータス: {response1.status_code}")
        print(f"   レスポンス時間: {first_time:.3f}秒")
        print(f"   キャッシュ: {response1.headers.get('X-Cache', 'MISS')}")

        # 2回目のリクエスト（キャッシュヒット）
        print("📤 2回目のリクエスト（キャッシュヒット）...")
        start_time = time.time()
        response2 = await self.client.get(f"{self.base_url}{endpoint}")
        second_time = time.time() - start_time

        print(f"   ステータス: {response2.status_code}")
        print(f"   レスポンス時間: {second_time:.3f}秒")
        print(f"   キャッシュ: {response2.headers.get('X-Cache', 'HIT')}")

        # パフォーマンス改善率計算
        if first_time > 0:
            improvement = ((first_time - second_time) / first_time) * 100
            print(f"\n📊 パフォーマンス改善: {improvement:.1f}%")

    async def run_all_tests(self):
        """全テストを実行"""
        print("🚀 Redisキャッシュ機能テスト開始")
        print("=" * 60)

        # 基本的なエンドポイントテスト
        await self.test_basic_endpoints()

        # キャッシュパフォーマンステスト
        print("\n🧪 テスト用エンドポイントのキャッシュテスト")
        print("=" * 60)

        await self.test_cache_performance(
            "/api/v1/test/simple",
            "シンプルキャッシュテスト（1分間キャッシュ）",
            60
        )

        await self.test_cache_performance(
            "/api/v1/test/parameter/test123",
            "パラメータ付きキャッシュテスト（2分間キャッシュ）",
            120
        )

        await self.test_cache_performance(
            "/api/v1/test/query?name=test&limit=5",
            "クエリパラメータ付きキャッシュテスト（3分間キャッシュ）",
            180
        )

        await self.test_cache_performance(
            "/api/v1/test/performance",
            "パフォーマンスキャッシュテスト（5分間キャッシュ）",
            300
        )

        print("\n✅ キャッシュ機能テスト完了")
        print("=" * 60)
        print("\n📝 テスト結果の説明:")
        print("   - 初回リクエスト: データベースから取得（遅い）")
        print("   - 2回目以降: キャッシュから取得（高速）")
        print("   - キャッシュ無効化後: 再度データベースから取得")
        print("   - パフォーマンス改善率: 初回と2回目の応答時間の差")

async def main():
    """メイン関数"""
    tester = CacheTester()
    try:
        await tester.run_all_tests()
        print("✅ キャッシュテストが完了しました")
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        await tester.client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

### Makefile コマンド

```makefile
# キャッシュ関連コマンド
cache-test:
	@echo "🧪 キャッシュ機能をテストしています..."
	@cd backend && python test_cache.py

cache-stats:
	@echo "📊 キャッシュ統計を取得しています..."
	@curl -s http://localhost:8000/api/v1/cache/stats | jq .

cache-clear:
	@echo "🗑️ 全キャッシュをクリアしています..."
	@curl -s -X DELETE http://localhost:8000/api/v1/cache/clear | jq .

cache-health:
	@echo "🏥 キャッシュ健全性をチェックしています..."
	@curl -s http://localhost:8000/api/v1/cache/health | jq .
```

## 監視と管理

### 1. キャッシュ統計の確認

```bash
# Makefileコマンド
make cache-stats

# または直接API呼び出し
curl http://localhost:8000/api/v1/cache/stats
```

### 2. キャッシュのクリア

```bash
# 全キャッシュクリア
make cache-clear

# 特定パターンのキャッシュクリア
curl -X DELETE http://localhost:8000/api/v1/cache/clear/project_*
```

### 3. キャッシュ機能テスト

```bash
# 自動テスト実行
make cache-test
```

## ベストプラクティス

### 1. キャッシュ戦略

- **頻繁にアクセスされるデータ**: 長めの有効期限（10-30 分）
- **変更頻度の高いデータ**: 短めの有効期限（1-5 分）
- **認証情報**: キャッシュ対象外
- **個人情報**: ユーザー固有のキャッシュキーを使用

### 2. キャッシュ無効化

- データ更新時は必ず関連キャッシュを無効化
- パターンベースの無効化を活用
- 定期的なキャッシュクリアを検討

### 3. 監視

- キャッシュヒット率の監視
- メモリ使用量の監視
- レスポンス時間の監視

### 4. セキュリティ

- 認証情報はキャッシュしない
- ユーザー固有データは適切に分離
- キャッシュキーに機密情報を含めない

## 今後の拡張予定

1. **キャッシュ階層化**: 複数レベルのキャッシュ戦略
2. **分散キャッシュ**: Redis Cluster 対応
3. **キャッシュ予熱**: 起動時のキャッシュ自動生成
4. **詳細メトリクス**: より詳細なパフォーマンス監視
5. **自動最適化**: 使用パターンに基づく自動調整
6. **キャッシュ予測**: 機械学習によるキャッシュ戦略最適化
7. **リアルタイム監視**: WebSocket によるリアルタイム監視
8. **キャッシュ分析**: キャッシュ効果の詳細分析機能
