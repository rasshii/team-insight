"""
JWT 失効管理 (Redis revocation list)

組織切替やログアウト時に refresh token を即座に失効させるための仕組み。

設計:
- Redis キー `auth:revoked:<jti>` に bool 値を保存し、TTL は token の残有効期間
- middleware でログイン認証時に jti を照合し、失効済なら 401 を返す

Note:
    アクセストークンは短命 (15 分) のため、revocation list には載せない。
    Refresh token のみ対象とする (組織切替・ログアウト時に旧 refresh を失効)。
"""

import logging
from typing import Optional

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


_REVOKED_KEY_PREFIX = "auth:revoked:"


def _key(jti: str) -> str:
    return f"{_REVOKED_KEY_PREFIX}{jti}"


async def revoke_refresh_token(jti: str, ttl_seconds: int) -> None:
    """
    refresh token を失効リストに登録する

    Args:
        jti: JWT ID (jti クレーム)
        ttl_seconds: 失効リストに保持する秒数 (token の残有効期間)
    """
    if ttl_seconds <= 0:
        return
    client = await redis_client.get_connection()
    await client.setex(_key(jti), ttl_seconds, "1")
    logger.info(f"Refresh token revoked: jti={jti}, ttl={ttl_seconds}s")


async def is_refresh_token_revoked(jti: Optional[str]) -> bool:
    """
    refresh token が失効済かチェック

    Args:
        jti: JWT ID。None の場合は失効していないとみなす (旧形式トークン互換)

    Returns:
        bool: 失効済なら True
    """
    if not jti:
        return False
    client = await redis_client.get_connection()
    return await client.exists(_key(jti)) > 0
