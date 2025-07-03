#!/usr/bin/env python3
"""
Backlog設定画面の動作確認スクリプト
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

async def test_connection_status(token: str):
    """接続状態を確認"""
    print("\n=== 接続状態の確認 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/sync/connection/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"接続状態: {data['status']}")
            print(f"メッセージ: {data['message']}")
            if data.get('expires_at'):
                print(f"有効期限: {data['expires_at']}")
            if data.get('last_project_sync'):
                print(f"最終プロジェクト同期: {data['last_project_sync']}")
            if data.get('last_task_sync'):
                print(f"最終タスク同期: {data['last_task_sync']}")
        else:
            print(f"エラー: {response.status_code} - {response.text}")

async def test_sync_history(token: str):
    """同期履歴を確認"""
    print("\n=== 同期履歴の確認 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/sync/history",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 7, "limit": 10}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"総件数: {data['total']}")
            print(f"履歴件数: {len(data['histories'])}")
            
            for history in data['histories']:
                print(f"\n- ID: {history['id']}")
                print(f"  タイプ: {history['sync_type']}")
                print(f"  ステータス: {history['status']}")
                print(f"  対象: {history.get('target_name', 'なし')}")
                print(f"  開始: {history.get('started_at', 'なし')}")
                if history['status'] == 'COMPLETED':
                    print(f"  作成: {history.get('items_created', 0)}件")
                    print(f"  更新: {history.get('items_updated', 0)}件")
                elif history['status'] == 'FAILED':
                    print(f"  エラー: {history.get('error_message', 'なし')}")
        else:
            print(f"エラー: {response.status_code} - {response.text}")

async def test_sync_user_tasks(token: str):
    """ユーザータスクの同期をテスト"""
    print("\n=== ユーザータスクの同期 ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/sync/user/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"メッセージ: {data['message']}")
            print(f"ステータス: {data['status']}")
        else:
            print(f"エラー: {response.status_code} - {response.text}")

async def main():
    # 認証情報を取得（実際の使用時は環境変数やコマンドライン引数から取得）
    print("Backlog設定画面のテスト")
    print("=" * 50)
    
    # テスト用のトークン（実際のトークンに置き換える必要があります）
    token = "YOUR_ACCESS_TOKEN_HERE"
    
    print("\n注意: このスクリプトを実行するには、有効なアクセストークンが必要です。")
    print("1. http://localhost:3000/auth/login からログイン")
    print("2. ブラウザの開発者ツールでlocalStorageから'team_insight_token'を取得")
    print("3. このスクリプトのtoken変数に設定")
    
    # 実際のテストを実行する場合は、以下のコメントを外してください
    # await test_connection_status(token)
    # await test_sync_history(token)
    # await test_sync_user_tasks(token)
    
    print("\n\nBacklog設定画面の機能:")
    print("1. 接続状態の確認 - /api/v1/sync/connection/status")
    print("2. 同期履歴の表示 - /api/v1/sync/history")
    print("3. プロジェクト同期 - /api/v1/sync/projects/all")
    print("4. タスク同期 - /api/v1/sync/user/tasks")
    print("5. 接続/切断 - Backlog OAuth認証フロー")

if __name__ == "__main__":
    asyncio.run(main())