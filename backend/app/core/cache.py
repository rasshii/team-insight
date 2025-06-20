"""
キャッシュ機能

このモジュールは、APIレスポンスのキャッシュ機能を提供します。
デコレータとミドルウェアを使用して、FastAPIエンドポイントの
レスポンスを自動的にキャッシュします。
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
    prefix: str,
    expire: Union[int, timedelta] = 300,  # デフォルト5分
    key_generator: Optional[Callable] = None
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
        self,
        app,
        default_expire: int = 300,
        cacheable_paths: Optional[list] = None,
        exclude_paths: Optional[list] = None
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
            return JSONResponse(
                content=cached_response,
                headers={"X-Cache": "HIT"}
            )

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

                # レスポンスを再構築
                return JSONResponse(
                    content=content,
                    headers={"X-Cache": "MISS"}
                )

            except Exception as e:
                logger.error(f"キャッシュ保存エラー: {e}")
                # エラー時は元のレスポンスを返す
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )

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
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]

        # ヘッダーからユーザー情報を取得（認証済みユーザーの場合）
        user_id = request.headers.get("X-User-ID")
        if user_id:
            key_parts.append(f"user:{user_id}")

        key_string = "|".join(key_parts)
        return f"cache:http:{hashlib.md5(key_string.encode()).hexdigest()}"

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

    return {
        "message": f"キャッシュクリア完了",
        "pattern": pattern,
        "deleted_count": deleted_count
    }
