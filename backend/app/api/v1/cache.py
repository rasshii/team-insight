"""
キャッシュ管理API

このモジュールは、Redisキャッシュの管理機能を提供します。
キャッシュ統計の表示、キャッシュのクリア、キャッシュ状態の確認などの機能を含みます。
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from app.core.cache import get_cache_stats, clear_cache
from app.core.security import get_current_active_superuser
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stats")
async def get_cache_statistics(current_user: User = Depends(get_current_active_superuser)) -> Dict[str, Any]:
    """
    キャッシュの統計情報を取得します

    このエンドポイントは、Redisキャッシュの詳細な統計情報を提供します。
    ヒット率、メモリ使用量、接続数などの情報を含みます。

    Args:
        current_user: 現在の認証済みユーザー（スーパーユーザーのみアクセス可能）

    Returns:
        キャッシュ統計情報

    Raises:
        HTTPException: 権限が不足している場合
    """
    try:
        stats = await get_cache_stats()

        # 統計情報に説明を追加
        stats_with_description = {
            "total_connections_received": {
                "value": stats.get("total_connections_received", 0),
                "description": "Redisへの総接続数",
            },
            "total_commands_processed": {
                "value": stats.get("total_commands_processed", 0),
                "description": "処理された総コマンド数",
            },
            "keyspace_hits": {"value": stats.get("keyspace_hits", 0), "description": "キャッシュヒット数"},
            "keyspace_misses": {"value": stats.get("keyspace_misses", 0), "description": "キャッシュミス数"},
            "hit_rate_percent": {"value": stats.get("hit_rate_percent", 0), "description": "キャッシュヒット率（%）"},
            "used_memory_human": {"value": stats.get("used_memory_human", "0B"), "description": "使用メモリ量"},
            "connected_clients": {"value": stats.get("connected_clients", 0), "description": "現在の接続クライアント数"},
        }

        logger.info(f"キャッシュ統計取得: ユーザー {current_user.email}")

        return {
            "message": "キャッシュ統計情報を取得しました",
            "data": stats_with_description,
            "summary": {
                "hit_rate": f"{stats.get('hit_rate_percent', 0)}%",
                "total_requests": stats.get("keyspace_hits", 0) + stats.get("keyspace_misses", 0),
                "memory_usage": stats.get("used_memory_human", "0B"),
            },
        }

    except Exception as e:
        logger.error(f"キャッシュ統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュ統計の取得に失敗しました")


@router.delete("/clear")
async def clear_all_cache(current_user: User = Depends(get_current_active_superuser)) -> Dict[str, Any]:
    """
    全キャッシュをクリアします

    このエンドポイントは、Redisに保存されている全てのキャッシュを削除します。
    注意: この操作は取り消しできません。

    Args:
        current_user: 現在の認証済みユーザー（スーパーユーザーのみアクセス可能）

    Returns:
        クリア結果

    Raises:
        HTTPException: 権限が不足している場合
    """
    try:
        result = await clear_cache("cache:*")

        logger.warning(f"全キャッシュクリア実行: ユーザー {current_user.email}, 削除件数: {result['deleted_count']}")

        return {
            "message": "全キャッシュをクリアしました",
            "deleted_count": result["deleted_count"],
            "pattern": result["pattern"],
            "warning": "この操作により、全てのキャッシュが削除されました。次回のリクエストはデータベースから取得されます。",
        }

    except Exception as e:
        logger.error(f"キャッシュクリアエラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュのクリアに失敗しました")


@router.delete("/clear/{pattern}")
async def clear_cache_by_pattern(pattern: str, current_user: User = Depends(get_current_active_superuser)) -> Dict[str, Any]:
    """
    指定されたパターンに一致するキャッシュをクリアします

    このエンドポイントは、指定されたパターンに一致するキャッシュキーのみを削除します。
    例: /cache/clear/user_profile:* でユーザープロフィール関連のキャッシュを削除

    Args:
        pattern: 削除するキャッシュキーのパターン
        current_user: 現在の認証済みユーザー（スーパーユーザーのみアクセス可能）

    Returns:
        クリア結果

    Raises:
        HTTPException: 権限が不足している場合
    """
    try:
        # パターンの検証（セキュリティ対策）
        if not pattern.startswith("cache:"):
            pattern = f"cache:{pattern}"

        result = await clear_cache(pattern)

        logger.info(
            f"パターンキャッシュクリア実行: ユーザー {current_user.email}, パターン: {pattern}, 削除件数: {result['deleted_count']}"
        )

        return {
            "message": f"パターン '{pattern}' に一致するキャッシュをクリアしました",
            "deleted_count": result["deleted_count"],
            "pattern": result["pattern"],
        }

    except Exception as e:
        logger.error(f"パターンキャッシュクリアエラー: {e}")
        raise HTTPException(status_code=500, detail="キャッシュのクリアに失敗しました")


@router.get("/health")
async def cache_health_check() -> Dict[str, Any]:
    """
    キャッシュの健全性チェック

    このエンドポイントは、Redisキャッシュの接続状態を確認します。
    認証不要でアクセス可能です。

    Returns:
        キャッシュの健全性情報
    """
    try:
        from app.core.redis_client import redis_client

        # Redis接続テスト
        redis_conn = await redis_client.get_connection()
        await redis_conn.ping()

        # 基本的な統計情報を取得
        stats = await get_cache_stats()

        return {
            "status": "healthy",
            "message": "Redisキャッシュは正常に動作しています",
            "connected_clients": stats.get("connected_clients", 0),
            "memory_usage": stats.get("used_memory_human", "0B"),
        }

    except Exception as e:
        logger.error(f"キャッシュ健全性チェックエラー: {e}")
        return {"status": "unhealthy", "message": "Redisキャッシュに接続できません", "error": str(e)}
