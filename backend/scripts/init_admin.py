#!/usr/bin/env python3
"""
初期管理者設定スクリプト

環境変数INITIAL_ADMIN_EMAILSから初期管理者を設定します。
通常はDockerコンテナ起動時に自動実行されます。

使用例:
    INITIAL_ADMIN_EMAILS=admin@example.com,manager@example.com python scripts/init_admin.py
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.core.config import settings


def init_admin_users():
    """環境変数から初期管理者を設定"""
    # 環境変数から初期管理者のメールアドレスを取得
    initial_admin_emails = os.getenv("INITIAL_ADMIN_EMAILS", "")
    
    if not initial_admin_emails:
        print("ℹ️  INITIAL_ADMIN_EMAILSが設定されていません。スキップします。")
        return
    
    # カンマ区切りでメールアドレスを分割
    admin_emails = [email.strip() for email in initial_admin_emails.split(",") if email.strip()]
    
    if not admin_emails:
        print("ℹ️  有効なメールアドレスが見つかりません。スキップします。")
        return
    
    db = SessionLocal()
    try:
        print(f"🔧 初期管理者を設定します: {', '.join(admin_emails)}")
        
        for email in admin_emails:
            # ユーザーを検索
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                print(f"⚠️  ユーザーが見つかりません: {email}")
                continue
            
            # 既にADMINロールを持っているか確認
            existing_admin = db.query(UserRole).join(Role).filter(
                UserRole.user_id == user.id,
                Role.name == "ADMIN"
            ).first()
            
            if existing_admin:
                print(f"ℹ️  {email} は既に管理者です")
                continue
            
            # ADMINロールを付与
            try:
                # ADMINロールを取得
                admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
                if not admin_role:
                    print(f"❌ ADMINロールが見つかりません。マイグレーションを実行してください。")
                    continue
                
                # UserRoleを作成
                user_role = UserRole(
                    user_id=user.id,
                    role_id=admin_role.id
                )
                db.add(user_role)
                db.commit()
                print(f"✅ {email} を管理者に設定しました")
            except Exception as e:
                print(f"❌ {email} の管理者設定に失敗: {str(e)}")
                db.rollback()
                continue
        
        print("✨ 初期管理者の設定が完了しました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


def main():
    """メイン処理"""
    print("=" * 60)
    print("Team Insight 初期管理者設定")
    print("=" * 60)
    
    init_admin_users()
    
    print("=" * 60)


if __name__ == "__main__":
    main()