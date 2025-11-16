"""
Redis接続クライアント

このモジュールは、Redisへの接続とキャッシュ操作を管理します。
接続プール、キャッシュの取得・設定・削除などの機能を提供します。
"""

import json
import hashlib
import logging
from typing import Optional, Any, Union, Dict, List
from datetime import timedelta
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis接続とキャッシュ操作を管理するクラス

    このクラスは、Redisへの接続プール管理と
    キャッシュの取得・設定・削除などの操作を提供します。
    """

    def __init__(self):
        """Redisクライアントの初期化"""
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self._redis_client: Optional[redis.Redis] = None

    async def get_connection(self) -> redis.Redis:
        """
        Redis接続を取得します

        Returns:
            Redisクライアントインスタンス
        """
        if self._redis_client is None:
            if self._redis_pool is None:
                # 接続プールの作成
                self._redis_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    password=settings.REDISCLI_AUTH,
                    decode_responses=True,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30,
                )

            self._redis_client = redis.Redis(connection_pool=self._redis_pool)

            # 接続テスト
            try:
                await self._redis_client.ping()
                logger.info("Redis接続が確立されました")
            except Exception as e:
                logger.error(f"Redis接続エラー: {e}")
                raise

        return self._redis_client

    async def close(self):
        """Redis接続を閉じます"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

        if self._redis_pool:
            await self._redis_pool.disconnect()
            self._redis_pool = None

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        キャッシュキーを生成します

        Args:
            prefix: キャッシュキーのプレフィックス
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            生成されたキャッシュキー
        """
        # 引数を文字列に変換
        key_parts = [prefix]

        # 位置引数を追加
        for arg in args:
            key_parts.append(str(arg))

        # キーワード引数をソートして追加
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")

        # キーを結合してハッシュ化
        key_string = "|".join(key_parts)
        return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから値を取得します

        Args:
            key: キャッシュキー

        Returns:
            キャッシュされた値（存在しない場合はNone）
        """
        try:
            redis_client = await self.get_connection()
            value = await redis_client.get(key)

            if value is None:
                return None

            # JSONとしてデコード
            return json.loads(value)

        except Exception as e:
            logger.error(f"キャッシュ取得エラー (key: {key}): {e}")
            return None

    async def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """
        キャッシュに値を設定します

        Args:
            key: キャッシュキー
            value: キャッシュする値
            expire: 有効期限（秒数またはtimedelta）

        Returns:
            設定が成功した場合True
        """
        try:
            redis_client = await self.get_connection()

            # 値をJSONとしてエンコード
            json_value = json.dumps(value, ensure_ascii=False, default=str)

            # 有効期限の設定
            if isinstance(expire, timedelta):
                expire_seconds = int(expire.total_seconds())
            else:
                expire_seconds = expire

            if expire_seconds:
                await redis_client.setex(key, expire_seconds, json_value)
            else:
                await redis_client.set(key, json_value)

            logger.debug(f"キャッシュ設定完了 (key: {key}, expire: {expire_seconds}s)")
            return True

        except Exception as e:
            logger.error(f"キャッシュ設定エラー (key: {key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        キャッシュから値を削除します

        Args:
            key: キャッシュキー

        Returns:
            削除が成功した場合True
        """
        try:
            redis_client = await self.get_connection()
            result = await redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"キャッシュ削除エラー (key: {key}): {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        パターンに一致するキャッシュキーを削除します

        Args:
            pattern: 削除するキーのパターン（例: "cache:user:*"）

        Returns:
            削除されたキーの数
        """
        try:
            redis_client = await self.get_connection()
            keys = await redis_client.keys(pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                logger.info(f"パターン削除完了 (pattern: {pattern}, deleted: {deleted})")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"パターン削除エラー (pattern: {pattern}): {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        キャッシュキーが存在するかチェックします

        Args:
            key: キャッシュキー

        Returns:
            キーが存在する場合True
        """
        try:
            redis_client = await self.get_connection()
            return await redis_client.exists(key) > 0

        except Exception as e:
            logger.error(f"キャッシュ存在チェックエラー (key: {key}): {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得します

        Returns:
            キャッシュ統計情報
        """
        try:
            redis_client = await self.get_connection()
            info = await redis_client.info()

            return {
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(f"キャッシュ統計取得エラー: {e}")
            return {}


# グローバルRedisクライアントインスタンス
redis_client = RedisClient()
