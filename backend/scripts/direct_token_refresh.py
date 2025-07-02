#!/usr/bin/env python3
"""
直接HTTPXでBacklogトークンをリフレッシュ
"""
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
import os
import psycopg2
from psycopg2.extras import RealDictCursor

async def refresh_backlog_token():
    """直接Backlog APIでトークンをリフレッシュ"""
    
    # 環境変数から設定を取得
    BACKLOG_CLIENT_ID = os.getenv("BACKLOG_CLIENT_ID")
    BACKLOG_CLIENT_SECRET = os.getenv("BACKLOG_CLIENT_SECRET")
    BACKLOG_SPACE_KEY = os.getenv("BACKLOG_SPACE_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://team_insight_user:team_insight_password@postgres:5432/team_insight")
    
    # データベース接続
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 現在のトークンを取得
        cur.execute("""
            SELECT id, user_id, access_token, refresh_token, expires_at, backlog_space_key
            FROM team_insight.oauth_tokens
            WHERE user_id = 1 AND provider = 'backlog'
        """)
        token_row = cur.fetchone()
        
        if not token_row:
            print("❌ No token found for user_id=1")
            return
        
        print("=== Current Token Status ===")
        print(f"User ID: {token_row['user_id']}")
        print(f"Expires at: {token_row['expires_at']}")
        # expires_atはnaive datetimeなので、UTCとして扱う
        expires_at_utc = token_row['expires_at'].replace(tzinfo=timezone.utc) if token_row['expires_at'].tzinfo is None else token_row['expires_at']
        print(f"Is expired: {expires_at_utc < datetime.now(timezone.utc)}")
        
        # リフレッシュトークンで更新
        space_key = token_row['backlog_space_key'] or BACKLOG_SPACE_KEY
        refresh_url = f"https://{space_key}.backlog.jp/api/v2/oauth2/token"
        
        print(f"\n=== Refreshing Token ===")
        print(f"Space key: {space_key}")
        print(f"Refresh URL: {refresh_url}")
        
        async with httpx.AsyncClient() as client:
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": token_row['refresh_token'],
                "client_id": BACKLOG_CLIENT_ID,
                "client_secret": BACKLOG_CLIENT_SECRET
            }
            
            response = await client.post(refresh_url, data=refresh_data)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Token refreshed successfully!")
                
                # 新しい有効期限を計算
                new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
                
                # データベースを更新
                cur.execute("""
                    UPDATE team_insight.oauth_tokens
                    SET access_token = %s,
                        refresh_token = %s,
                        expires_at = %s,
                        updated_at = %s
                    WHERE id = %s
                """, (
                    token_data["access_token"],
                    token_data["refresh_token"],
                    new_expires_at,
                    datetime.now(timezone.utc),
                    token_row['id']
                ))
                conn.commit()
                
                print(f"New expires_at: {new_expires_at}")
                
                # APIアクセステスト
                print("\n=== Testing API Access ===")
                api_url = f"https://{space_key}.backlog.jp/api/v2/users/myself"
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                
                test_response = await client.get(api_url, headers=headers)
                if test_response.status_code == 200:
                    user_info = test_response.json()
                    print(f"✅ API Access successful! User: {user_info.get('name', 'Unknown')}")
                else:
                    print(f"❌ API test failed: {test_response.status_code}")
                    
            else:
                print(f"❌ Token refresh failed: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    asyncio.run(refresh_backlog_token())