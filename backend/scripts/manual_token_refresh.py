#!/usr/bin/env python3
"""
手動でBacklogトークンをリフレッシュし、接続状態を確認する
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.auth import OAuthToken
from app.core.token_refresh import token_refresh_service
from app.core.config import settings
from app.services.backlog_client import BacklogClient
import httpx

async def test_token_refresh():
    """トークンリフレッシュと接続テスト"""
    db = SessionLocal()
    try:
        # ユーザーID 1のトークンを取得
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == 1,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not token:
            print("❌ No token found for user_id=1")
            return
        
        print("=== Current Token Status ===")
        print(f"User ID: {token.user_id}")
        print(f"Provider: {token.provider}")
        print(f"Expires at: {token.expires_at}")
        print(f"Is expired: {token.expires_at < datetime.now(timezone.utc)}")
        print(f"Space key: {token.backlog_space_key or settings.BACKLOG_SPACE_KEY}")
        
        # リフレッシュトークンで更新
        print("\n=== Refreshing Token ===")
        space_key = token.backlog_space_key or settings.BACKLOG_SPACE_KEY
        
        # 直接HTTPリクエストでリフレッシュ
        async with httpx.AsyncClient() as client:
            refresh_url = f"https://{space_key}.backlog.com/api/v2/oauth2/token"
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": settings.BACKLOG_CLIENT_ID,
                "client_secret": settings.BACKLOG_CLIENT_SECRET
            }
            
            print(f"Refresh URL: {refresh_url}")
            print(f"Client ID: {settings.BACKLOG_CLIENT_ID[:10]}...")
            
            response = await client.post(refresh_url, data=refresh_data)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Token refreshed successfully!")
                
                # トークンを更新
                token.access_token = token_data["access_token"]
                token.refresh_token = token_data["refresh_token"]
                token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
                token.updated_at = datetime.now(timezone.utc)
                db.commit()
                
                print(f"New expires_at: {token.expires_at}")
                
                # 新しいトークンでAPIテスト
                print("\n=== Testing API Access ===")
                client = BacklogClient(token.access_token, space_key)
                user_info = await client.get_user_info()
                print(f"✅ API Access successful! User: {user_info.get('name', 'Unknown')}")
                
            else:
                print(f"❌ Token refresh failed: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(test_token_refresh())