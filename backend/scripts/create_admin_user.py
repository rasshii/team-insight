#!/usr/bin/env python3
"""
管理者ユーザー作成スクリプト
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import get_password_hash

# 循環参照を避けるため、関数内でインポート
def get_models():
    from app.models.user import User
    from app.models.rbac import Role, UserRole
    # SyncHistoryを読み込んで関係を解決
    from app.models.sync_history import SyncHistory
    return User, Role, UserRole

def create_admin_user():
    """管理者ユーザーを作成"""
    
    User, Role, UserRole = get_models()
    db = SessionLocal()
    
    try:
        # 管理者ユーザーの情報
        admin_email = "admin@example.com"
        admin_password = "AdminPassword123!"
        admin_name = "System Administrator"
        
        # 既存のユーザーを確認
        existing_user = db.query(User).filter(User.email == admin_email).first()
        if existing_user:
            print(f"ユーザー {admin_email} は既に存在します")
            
            # パスワードを更新
            existing_user.hashed_password = get_password_hash(admin_password)
            existing_user.is_active = True
            existing_user.is_superuser = True
            existing_user.is_email_verified = True
            db.commit()
            print(f"パスワードとステータスを更新しました")
        else:
            # 新規ユーザーを作成
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                name=admin_name,
                is_active=True,
                is_superuser=True,
                is_email_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"管理者ユーザー {admin_email} を作成しました")
            existing_user = admin_user
        
        # ADMINロールを割り当て
        admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
        if admin_role:
            # 既存のロール割り当てを確認
            existing_assignment = db.query(UserRole).filter(
                UserRole.user_id == existing_user.id,
                UserRole.role_id == admin_role.id,
                UserRole.project_id == None
            ).first()
            
            if not existing_assignment:
                user_role = UserRole(
                    user_id=existing_user.id,
                    role_id=admin_role.id,
                    project_id=None  # グローバルロール
                )
                db.add(user_role)
                db.commit()
                print(f"ADMINロールを割り当てました")
            else:
                print(f"ADMINロールは既に割り当てられています")
        else:
            print("警告: ADMINロールが見つかりません")
        
        print("\n✅ 管理者ユーザーの準備が完了しました")
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()