"""
キャッシュ機能

このモジュールは、Redisを使用したAPIレスポンスのキャッシュ機能を提供します。
デコレータとミドルウェアを使用して、FastAPIエンドポイントのレスポンスを
自動的にキャッシュし、パフォーマンスを向上させます。

主要な機能:
    1. レスポンスキャッシュ
       - デコレータベースのキャッシュ（@cache_response）
       - ミドルウェアベースのキャッシュ（CacheMiddleware）
       - 自動的なキャッシュキー生成

    2. キャッシュ無効化
       - パターンマッチングによる一括削除
       - データ変更時の自動キャッシュクリア
       - デコレータベースの無効化（@cache_invalidate）

    3. キャッシュ統計
       - ヒット率の計算
       - キャッシュサイズの監視

主要なクラス・関数:
    - cache_response(): レスポンスキャッシュデコレータ
    - cache_invalidate(): キャッシュ無効化デコレータ
    - CacheMiddleware: HTTPキャッシュミドルウェア
    - get_cache_stats(): キャッシュ統計取得
    - clear_cache(): キャッシュクリア

キャッシュ戦略:
    - GETリクエストのみキャッシュ（読み取り専用）
    - POST/PUT/DELETE時に関連キャッシュを自動削除
    - TTL（Time To Live）でキャッシュの有効期限を管理
    - キーにユーザーIDを含めて個別キャッシュ

使用例:
    ```python
    from app.core.cache import cache_response, cache_invalidate

    # デコレータでキャッシュ（5分間）
    @router.get("/users/{user_id}")
    @cache_response("user_profile", expire=300)
    async def get_user(user_id: int):
        return get_user_from_db(user_id)

    # データ更新時にキャッシュを無効化
    @router.put("/users/{user_id}")
    @cache_invalidate("cache:user_profile:*")
    async def update_user(user_id: int, data: UserUpdate):
        return update_user_in_db(user_id, data)

    # ミドルウェアの設定
    app.add_middleware(
        CacheMiddleware,
        default_expire=300,  # 5分
        cacheable_paths=["/api/v1/"],
        exclude_paths=["/api/v1/auth/"]
    )
    ```

パフォーマンスの改善:
    - データベースクエリの削減
    - レスポンス時間の短縮
    - サーバー負荷の軽減

セキュリティの考慮事項:
    - 個人情報を含むレスポンスは慎重にキャッシュ
    - 認証トークンをキャッシュキーに含めてユーザー分離
    - 機密データはキャッシュしない、またはTTLを短く設定
"""

import functools
import hashlib
import json
import logging
from typing import Optional, Any, Union, Callable, Dict
from datetime import timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


def cache_response(
    prefix: str, expire: Union[int, timedelta] = 300, key_generator: Optional[Callable] = None  # デフォルト5分
):
    """
    APIレスポンスをキャッシュするデコレータ

    Args:
        prefix: キャッシュキーのプレフィックス
        expire: キャッシュの有効期限（秒数またはtimedelta）
        key_generator: カスタムキー生成関数

    Usage:
        @cache_response("user_profile", expire=600)
        async def get_user_profile(user_id: int):
            # この関数の結果がキャッシュされる
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキーの生成
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # デフォルトのキー生成
                key_parts = [prefix]

                # 位置引数を追加
                for arg in args:
                    key_parts.append(str(arg))

                # キーワード引数をソートして追加
                for key, value in sorted(kwargs.items()):
                    key_parts.append(f"{key}:{value}")

                key_string = "|".join(key_parts)
                cache_key = f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

            # キャッシュから取得を試行
            cached_result = await redis_client.get(cache_key)

            if cached_result is not None:
                logger.info(f"キャッシュヒット: {cache_key}")
                return cached_result

            # キャッシュミス - 関数を実行
            logger.info(f"キャッシュミス: {cache_key}")
            result = await func(*args, **kwargs)

            # 結果をキャッシュに保存
            await redis_client.set(cache_key, result, expire)

            return result

        return wrapper

    return decorator


def cache_invalidate(pattern: str):
    """
    キャッシュを無効化するデコレータ

    Args:
        pattern: 無効化するキャッシュキーのパターン

    Usage:
        @cache_invalidate("user_profile:*")
        async def update_user_profile(user_id: int):
            # この関数実行後にuser_profile関連のキャッシュが無効化される
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 関数を実行
            result = await func(*args, **kwargs)

            # キャッシュを無効化
            deleted_count = await redis_client.delete_pattern(pattern)
            logger.info(f"キャッシュ無効化完了: {pattern} ({deleted_count}件削除)")

            return result

        return wrapper

    return decorator


class CacheMiddleware(BaseHTTPMiddleware):
    """
    HTTPリクエストのキャッシュミドルウェア

    このミドルウェアは、GETリクエストのレスポンスを自動的にキャッシュします。
    """

    def __init__(
        self, app, default_expire: int = 300, cacheable_paths: Optional[list] = None, exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.default_expire = default_expire
        self.cacheable_paths = cacheable_paths or []
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):
        # GETリクエストのみキャッシュ対象
        if request.method != "GET":
            # POST/PUT/DELETEリクエストの場合、関連するキャッシュをクリア
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                await self._invalidate_related_cache(request)
            return await call_next(request)

        # パスチェック
        path = request.url.path

        # 除外パスチェック
        if any(path.startswith(exclude_path) for exclude_path in self.exclude_paths):
            return await call_next(request)

        # キャッシュ対象パスチェック
        if self.cacheable_paths and not any(path.startswith(cacheable_path) for cacheable_path in self.cacheable_paths):
            return await call_next(request)

        # キャッシュキーの生成
        cache_key = self._generate_cache_key(request)

        # キャッシュから取得を試行
        cached_response = await redis_client.get(cache_key)

        if cached_response is not None:
            logger.info(f"キャッシュヒット: {path}")
            # CORSヘッダーを含む基本的なヘッダーを設定
            headers = {
                "X-Cache": "HIT",
                "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
            return JSONResponse(content=cached_response, headers=headers)

        # キャッシュミス - レスポンスを取得
        logger.info(f"キャッシュミス: {path}")
        response = await call_next(request)

        # 成功レスポンスのみキャッシュ
        if response.status_code == 200:
            try:
                # レスポンスボディを取得
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # JSONとしてデコード
                content = json.loads(body.decode())

                # キャッシュに保存
                await redis_client.set(cache_key, content, self.default_expire)

                # 元のレスポンスのヘッダーを保持
                response_headers = dict(response.headers)
                response_headers["X-Cache"] = "MISS"

                # レスポンスを再構築
                return JSONResponse(content=content, headers=response_headers)

            except Exception as e:
                logger.error(f"キャッシュ保存エラー: {e}")
                # エラー時は元のレスポンスを返す
                return Response(content=body, status_code=response.status_code, headers=dict(response.headers))

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """
        リクエストからキャッシュキーを生成

        Args:
            request: FastAPIリクエストオブジェクト

        Returns:
            生成されたキャッシュキー
        """
        # パスとクエリパラメータを結合
        key_parts = [request.method, request.url.path, str(sorted(request.query_params.items()))]

        # ヘッダーからユーザー情報を取得（認証済みユーザーの場合）
        user_id = request.headers.get("X-User-ID")
        if user_id:
            key_parts.append(f"user:{user_id}")

        key_string = "|".join(key_parts)
        return f"cache:http:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def _invalidate_related_cache(self, request: Request):
        """
        変更操作時に関連するキャッシュを無効化
        """
        path = request.url.path
        logger.info(f"キャッシュ無効化開始: {request.method} {path}")

        # パスベースで関連するすべてのHTTPキャッシュをクリア
        try:
            # 特定のパスに関連する変更の場合は、すべてのHTTPキャッシュをクリア
            if any(keyword in path for keyword in ["/teams", "/users", "/projects", "/tasks"]):
                pattern = "cache:http:*"
                deleted_count = await redis_client.delete_pattern(pattern)
                if deleted_count > 0:
                    logger.info(f"キャッシュ無効化完了: {path} に関連する {deleted_count} 件のキャッシュを削除")
                else:
                    logger.info("削除対象のキャッシュがありません")
            else:
                logger.info(f"キャッシュ無効化スキップ: {path} は対象外")

        except Exception as e:
            logger.error(f"キャッシュ無効化エラー: {e}", exc_info=True)


# キャッシュ統計エンドポイント用のヘルパー関数
async def get_cache_stats() -> Dict[str, Any]:
    """
    キャッシュの統計情報を取得

    Returns:
        キャッシュ統計情報
    """
    stats = await redis_client.get_cache_stats()

    # ヒット率の計算
    hits = stats.get("keyspace_hits", 0)
    misses = stats.get("keyspace_misses", 0)
    total = hits + misses

    if total > 0:
        hit_rate = (hits / total) * 100
    else:
        hit_rate = 0

    stats["hit_rate_percent"] = round(hit_rate, 2)

    return stats


# キャッシュクリア用のヘルパー関数
async def clear_cache(pattern: str = "cache:*") -> Dict[str, Any]:
    """
    キャッシュをクリア

    Args:
        pattern: クリアするキャッシュキーのパターン

    Returns:
        クリア結果
    """
    deleted_count = await redis_client.delete_pattern(pattern)

    return {"message": f"キャッシュクリア完了", "pattern": pattern, "deleted_count": deleted_count}
