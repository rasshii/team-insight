#!/usr/bin/env python3
"""
キャッシュ機能テストスクリプト

このスクリプトは、Redisキャッシュ機能の動作をテストします。
実際のAPIエンドポイントにリクエストを送信して、キャッシュの動作を確認します。
"""

import asyncio
import httpx
import time
import json
from typing import Dict, Any, Optional

# テスト設定
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

async def test_cache_performance(client: httpx.AsyncClient, endpoint: str, description: str) -> Dict[str, Any]:
    """
    キャッシュパフォーマンスをテスト

    Args:
        client: httpxクライアント
        endpoint: テストするエンドポイント
        description: テストの説明

    Returns:
        テスト結果
    """
    print(f"\n🔍 {description}")
    print("=" * 50)

    # 初回リクエスト（キャッシュミス）
    print("📤 初回リクエスト（キャッシュミス）...")
    start_time = time.time()

    try:
        response = await client.get(f"{API_BASE}{endpoint}")
        first_response_time = time.time() - start_time
        first_status = response.status_code

        # キャッシュヘッダーを確認
        cache_header = response.headers.get("x-cache", "UNKNOWN")

        print(f"   ステータス: {first_status}")
        print(f"   レスポンス時間: {first_response_time:.3f}秒")
        print(f"   キャッシュ: {cache_header}")

        if first_status != 200:
            print(f"   ⚠️  レスポンス: {response.text[:100]}...")
            return {
                "description": description,
                "error": f"HTTP {first_status}",
                "first_request": {"time": first_response_time, "status": first_status}
            }

    except Exception as e:
        print(f"   ❌ 初回リクエストエラー: {e}")
        return {
            "description": description,
            "error": str(e)
        }

    # 2回目のリクエスト（キャッシュヒット）
    print("\n📤 2回目のリクエスト（キャッシュヒット）...")
    start_time = time.time()

    try:
        response = await client.get(f"{API_BASE}{endpoint}")
        second_response_time = time.time() - start_time
        second_status = response.status_code

        # キャッシュヘッダーを確認
        cache_header = response.headers.get("x-cache", "UNKNOWN")

        print(f"   ステータス: {second_status}")
        print(f"   レスポンス時間: {second_response_time:.3f}秒")
        print(f"   キャッシュ: {cache_header}")

    except Exception as e:
        print(f"   ❌ 2回目リクエストエラー: {e}")
        return {
            "description": description,
            "error": str(e)
        }

    # パフォーマンス改善を計算
    if first_response_time > 0:
        improvement = ((first_response_time - second_response_time) / first_response_time) * 100
    else:
        improvement = 0

    print(f"\n📊 パフォーマンス改善: {improvement:.1f}%")

    return {
        "description": description,
        "first_request": {
            "time": first_response_time,
            "status": first_status,
            "cache": cache_header
        },
        "second_request": {
            "time": second_response_time,
            "status": second_status,
            "cache": cache_header
        },
        "improvement_percent": improvement
    }

async def test_cache_management(client: httpx.AsyncClient) -> None:
    """
    キャッシュ管理機能をテスト

    Args:
        client: httpxクライアント
    """
    print(f"\n🔧 キャッシュ管理機能テスト")
    print("=" * 50)

    # キャッシュ統計の取得
    print("📊 キャッシュ統計を取得...")
    try:
        response = await client.get(f"{API_BASE}/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ヒット率: {stats.get('summary', {}).get('hit_rate', 'N/A')}")
            print(f"   総リクエスト数: {stats.get('summary', {}).get('total_requests', 'N/A')}")
            print(f"   メモリ使用量: {stats.get('summary', {}).get('memory_usage', 'N/A')}")
        else:
            print(f"   エラー: {response.status_code} - {response.text[:100]}...")
    except Exception as e:
        print(f"   エラー: {e}")

    # キャッシュ健全性チェック
    print("\n🏥 キャッシュ健全性チェック...")
    try:
        response = await client.get(f"{API_BASE}/cache/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ステータス: {health.get('status', 'N/A')}")
            print(f"   メッセージ: {health.get('message', 'N/A')}")
        else:
            print(f"   エラー: {response.status_code}")
    except Exception as e:
        print(f"   エラー: {e}")

async def test_cache_invalidation(client: httpx.AsyncClient) -> None:
    """
    キャッシュ無効化機能をテスト

    Args:
        client: httpxクライアント
    """
    print(f"\n🗑️ キャッシュ無効化テスト")
    print("=" * 50)

    # テスト用エンドポイントを取得（キャッシュされる）
    print("📤 テストエンドポイントを取得（キャッシュ作成）...")
    try:
        response = await client.get(f"{API_BASE}/test/cache/simple")
        if response.status_code == 200:
            print("   ✅ テストエンドポイント取得成功")
        else:
            print(f"   ❌ エラー: {response.status_code} - {response.text[:100]}...")
            return
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        return

    # キャッシュ無効化
    print("\n🗑️ テストキャッシュを無効化...")
    try:
        response = await client.post(f"{API_BASE}/test/cache/invalidate")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ キャッシュ無効化成功: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ エラー: {response.status_code} - {response.text[:100]}...")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

async def test_basic_endpoints(client: httpx.AsyncClient) -> None:
    """
    基本的なエンドポイントのテスト

    Args:
        client: httpxクライアント
    """
    print(f"\n🌐 基本的なエンドポイントテスト")
    print("=" * 50)

    # ルートエンドポイント
    print("📤 ルートエンドポイント...")
    try:
        response = await client.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功: {data.get('message', 'N/A')}")
        else:
            print(f"   ❌ エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # ヘルスチェック
    print("\n📤 ヘルスチェック...")
    try:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ アプリケーション: {health.get('status', 'N/A')}")
            print(f"   ✅ Redis: {health.get('services', {}).get('redis', 'N/A')}")
        else:
            print(f"   ❌ エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

async def test_public_endpoints(client: httpx.AsyncClient) -> None:
    """
    認証不要なエンドポイントのテスト

    Args:
        client: httpxクライアント
    """
    print(f"\n🌐 認証不要エンドポイントテスト")
    print("=" * 50)

    # APIドキュメント
    print("📤 APIドキュメント...")
    try:
        response = await client.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("   ✅ APIドキュメント取得成功")
        else:
            print(f"   ❌ エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # テスト用キャッシュ統計
    print("\n📤 テスト用キャッシュ統計...")
    try:
        response = await client.get(f"{API_BASE}/test/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ テストエンドポイント数: {stats.get('stats', {}).get('total_endpoints', 'N/A')}")
        else:
            print(f"   ❌ エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

async def main():
    """
    メイン関数
    """
    print("🚀 Redisキャッシュ機能テスト開始")
    print("=" * 60)

    # httpxクライアント作成
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 基本的なエンドポイントテスト
            await test_basic_endpoints(client)

            # 認証不要なエンドポイントテスト
            await test_public_endpoints(client)

            # キャッシュ管理機能テスト
            await test_cache_management(client)

            # テスト用エンドポイントのキャッシュテスト
            print("\n🧪 テスト用エンドポイントのキャッシュテスト")
            print("=" * 60)

            # シンプルキャッシュテスト
            await test_cache_performance(
                client,
                "/test/cache/simple",
                "シンプルキャッシュテスト（1分間キャッシュ）"
            )

            # パラメータ付きキャッシュテスト
            await test_cache_performance(
                client,
                "/test/cache/parameter/1",
                "パラメータ付きキャッシュテスト（2分間キャッシュ）"
            )

            # クエリパラメータ付きキャッシュテスト
            await test_cache_performance(
                client,
                "/test/cache/query?page=1&limit=5",
                "クエリパラメータ付きキャッシュテスト（3分間キャッシュ）"
            )

            # パフォーマンスキャッシュテスト
            await test_cache_performance(
                client,
                "/test/cache/performance",
                "パフォーマンスキャッシュテスト（5分間キャッシュ）"
            )

            # キャッシュ無効化テスト
            await test_cache_invalidation(client)

            print(f"\n✅ キャッシュ機能テスト完了")
            print("=" * 60)
            print("\n📝 テスト結果の説明:")
            print("   - 初回リクエスト: データベースから取得（遅い）")
            print("   - 2回目以降: キャッシュから取得（高速）")
            print("   - キャッシュ無効化後: 再度データベースから取得")
            print("   - パフォーマンス改善率: 初回と2回目の応答時間の差")

        except Exception as e:
            print(f"\n❌ テストエラー: {e}")
            print("=" * 60)

if __name__ == "__main__":
    # 非同期実行
    asyncio.run(main())
