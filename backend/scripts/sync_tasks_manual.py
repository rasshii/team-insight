#!/usr/bin/env python3
"""
手動でタスクを同期するスクリプト
開発環境でBacklogからタスクデータを同期します。
"""

import sys
import os
import asyncio
from datetime import datetime

# プロジェクトルートのパスをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.auth import OAuthToken
from app.services.sync_service import sync_service
from app.core.config import settings

async def sync_user_tasks_manual():
    """ユーザーのタスクを手動で同期"""
    db = SessionLocal()
    
    try:
        # ユーザーID 1のユーザーを取得
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("❌ ユーザーID 1が見つかりません")
            return
        
        print(f"✅ ユーザー情報: {user.name} ({user.email})")
        
        # OAuthトークンを取得
        oauth_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not oauth_token:
            print("❌ Backlog OAuthトークンが見つかりません")
            return
        
        print(f"✅ OAuthトークン取得")
        print(f"   - 有効期限: {oauth_token.expires_at}")
        print(f"   - 現在時刻: {datetime.utcnow()}")
        
        if oauth_token.is_expired():
            print("⚠️  トークンの有効期限が切れています")
            print("🔄 トークンのリフレッシュを試みます...")
            
            # トークンリフレッシュを試行
            from app.core.token_refresh import token_refresh_service
            try:
                space_key = oauth_token.backlog_space_key or settings.BACKLOG_SPACE_KEY
                refreshed_token = await token_refresh_service.refresh_token(oauth_token, db, space_key)
                if refreshed_token:
                    oauth_token = refreshed_token
                    print("✅ トークンのリフレッシュに成功しました")
                    print(f"   - 新しい有効期限: {oauth_token.expires_at}")
                else:
                    print("❌ トークンのリフレッシュに失敗しました")
                    return
            except Exception as e:
                print(f"❌ トークンリフレッシュエラー: {str(e)}")
                return
        
        print("\n🔄 タスクの同期を開始します...")
        
        # 同期サービスを使用してタスクを同期
        result = await sync_service.sync_user_tasks(
            user,
            oauth_token.access_token,
            db
        )
        
        print(f"\n✅ 同期完了！")
        print(f"   - 新規作成: {result['created']}件")
        print(f"   - 更新: {result['updated']}件")
        print(f"   - エラー: {result['errors']}件")
        print(f"   - 合計: {result['total']}件")
        
        # 同期後のタスク数を確認
        from app.models.task import Task
        user_tasks = db.query(Task).filter(Task.assignee_id == user.id).count()
        print(f"\n📊 ユーザー {user.name} に割り当てられたタスク総数: {user_tasks}件")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Backlogタスク手動同期スクリプト\n")
    asyncio.run(sync_user_tasks_manual())