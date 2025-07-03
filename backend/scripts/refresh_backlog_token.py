#!/usr/bin/env python3
"""
Backlogトークンを手動でリフレッシュするスクリプト
"""
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.auth import OAuthToken
from app.core.token_refresh import token_refresh_service
from app.core.config import settings
from datetime import datetime, timezone

async def refresh_user_token(user_id: int):
    """指定ユーザーのBacklogトークンをリフレッシュ"""
    db = SessionLocal()
    try:
        # 現在のトークンを取得
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not token:
            print(f"No Backlog token found for user_id={user_id}")
            return
        
        print(f"Current token status:")
        print(f"  User ID: {token.user_id}")
        print(f"  Provider: {token.provider}")
        print(f"  Expires at: {token.expires_at}")
        print(f"  Is expired: {token.expires_at < datetime.now(timezone.utc)}")
        print(f"  Last used: {token.last_used_at}")
        print(f"  Space key: {token.backlog_space_key or settings.BACKLOG_SPACE_KEY}")
        
        # トークンをリフレッシュ
        print("\nRefreshing token...")
        space_key = token.backlog_space_key or settings.BACKLOG_SPACE_KEY
        refreshed = await token_refresh_service.refresh_token(token, db, space_key)
        
        if refreshed:
            print(f"\n✅ Token refreshed successfully!")
            print(f"  New expires_at: {refreshed.expires_at}")
            print(f"  Updated at: {refreshed.updated_at}")
        else:
            print("\n❌ Failed to refresh token")
            print("Check the logs for more details.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Refresh Backlog OAuth token")
    parser.add_argument("--user-id", type=int, default=1, help="User ID (default: 1)")
    args = parser.parse_args()
    
    asyncio.run(refresh_user_token(args.user_id))