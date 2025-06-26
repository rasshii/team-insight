"""
テスト用APIエンドポイント

このモジュールは、キャッシュ機能をテストするための認証不要なエンドポイントを提供します。
開発・テスト環境でのみ使用してください。
"""

import logging
import asyncio
from typing import Dict, Any
from fastapi import APIRouter
from datetime import datetime

from app.core.cache import cache_response, cache_invalidate

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/cache/simple")
@cache_response("test_simple", expire=60)  # 1分間キャッシュ
async def test_simple_cache() -> Dict[str, Any]:
    """
    シンプルなキャッシュテスト

    このエンドポイントは、基本的なキャッシュ機能をテストします。
    1分間キャッシュされ、2回目のリクエストからは高速で応答します。
    """
    # データベースアクセスをシミュレート（重い処理）
    await asyncio.sleep(0.5)  # 500msの遅延をシミュレート

    return {
        "message": "シンプルキャッシュテスト",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "id": 1,
            "name": "テストデータ",
            "description": "キャッシュ機能のテスト用データ"
        },
        "cached": True
    }

@router.get("/cache/parameter/{param_id}")
@cache_response("test_parameter", expire=120)  # 2分間キャッシュ
async def test_parameter_cache(param_id: int) -> Dict[str, Any]:
    """
    パラメータ付きキャッシュテスト

    このエンドポイントは、パラメータに基づくキャッシュ機能をテストします。
    各パラメータ値に対して個別にキャッシュされます。
    """
    # データベースアクセスをシミュレート（重い処理）
    await asyncio.sleep(0.3)  # 300msの遅延をシミュレート

    return {
        "message": "パラメータキャッシュテスト",
        "param_id": param_id,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "id": param_id,
            "name": f"パラメータ{param_id}のデータ",
            "value": param_id * 10,
            "description": f"パラメータ{param_id}用のキャッシュテストデータ"
        },
        "cached": True
    }

@router.get("/cache/query")
@cache_response("test_query", expire=180)  # 3分間キャッシュ
async def test_query_cache(
    page: int = 1,
    limit: int = 10,
    sort: str = "id"
) -> Dict[str, Any]:
    """
    クエリパラメータ付きキャッシュテスト

    このエンドポイントは、クエリパラメータに基づくキャッシュ機能をテストします。
    クエリパラメータの組み合わせごとに個別にキャッシュされます。
    """
    # データベースアクセスをシミュレート（重い処理）
    await asyncio.sleep(0.7)  # 700msの遅延をシミュレート

    # ページネーションをシミュレート
    start = (page - 1) * limit
    end = start + limit

    items = []
    for i in range(start, min(end, 100)):  # 最大100件まで
        items.append({
            "id": i + 1,
            "name": f"アイテム{i + 1}",
            "value": (i + 1) * 2,
            "created_at": datetime.now().isoformat()
        })

    return {
        "message": "クエリキャッシュテスト",
        "page": page,
        "limit": limit,
        "sort": sort,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "items": items,
            "total": 100,
            "page_info": {
                "current_page": page,
                "total_pages": 10,
                "has_next": page < 10,
                "has_prev": page > 1
            }
        },
        "cached": True
    }

@router.get("/cache/performance")
@cache_response("test_performance", expire=300)  # 5分間キャッシュ
async def test_performance_cache() -> Dict[str, Any]:
    """
    パフォーマンステスト用キャッシュ

    このエンドポイントは、キャッシュのパフォーマンス効果を測定するためのテストです。
    重い処理をシミュレートして、キャッシュの効果を明確に示します。
    """
    # 非常に重い処理をシミュレート
    await asyncio.sleep(1.0)  # 1秒の遅延をシミュレート

    # 複雑なデータ構造を生成
    complex_data = {
        "users": [
            {"id": i, "name": f"ユーザー{i}", "email": f"user{i}@example.com"}
            for i in range(1, 51)
        ],
        "projects": [
            {"id": i, "name": f"プロジェクト{i}", "status": "active"}
            for i in range(1, 21)
        ],
        "metrics": {
            "total_users": 50,
            "active_projects": 20,
            "completion_rate": 85.5,
            "avg_response_time": 0.15
        }
    }

    return {
        "message": "パフォーマンスキャッシュテスト",
        "timestamp": datetime.now().isoformat(),
        "processing_time": "1.0秒（シミュレート）",
        "data": complex_data,
        "cached": True
    }

@router.post("/cache/invalidate")
@cache_invalidate("test_*")  # test_で始まるキャッシュを無効化
async def test_cache_invalidation() -> Dict[str, Any]:
    """
    キャッシュ無効化テスト

    このエンドポイントは、キャッシュ無効化機能をテストします。
    実行後、test_で始まる全てのキャッシュが無効化されます。
    """
    return {
        "message": "テストキャッシュを無効化しました",
        "timestamp": datetime.now().isoformat(),
        "invalidated_pattern": "test_*",
        "cache_invalidated": True
    }

@router.get("/cache/stats")
async def test_cache_stats() -> Dict[str, Any]:
    """
    キャッシュ統計テスト

    このエンドポイントは、キャッシュの統計情報を返します。
    認証不要でアクセス可能です。
    """
    return {
        "message": "キャッシュ統計情報",
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "total_endpoints": 5,
            "cache_enabled": True,
            "default_expire": 300,
            "test_endpoints": [
                "/api/v1/test/cache/simple",
                "/api/v1/test/cache/parameter/{param_id}",
                "/api/v1/test/cache/query",
                "/api/v1/test/cache/performance"
            ]
        }
    }
