#!/usr/bin/env python3
"""テストユーザー作成スクリプト"""

import sys
sys.path.append('/app')

from app.db.session import SessionLocal
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.core.security import get_password_hash
from datetime import datetime, timezone

def create_test_user():
    """テストユーザーを作成"""
    db = SessionLocal()
    
    try:
        # テストユーザーが存在するか確認
        test_user = db.query(User).filter(User.email == 'test@example.com').first()
        
        if not test_user:
            # テストユーザー作成
            test_user = User(
                email='test@example.com',
                name='Test User',
                hashed_password=get_password_hash('password123'),
                is_active=True,
                is_email_verified=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            # MEMBERロールを割り当て
            member_role = db.query(Role).filter(Role.name == "MEMBER").first()
            if member_role:
                user_role = UserRole(
                    user_id=test_user.id,
                    role_id=member_role.id,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(user_role)
                db.commit()
            
            print('テストユーザーを作成しました')
            print('Email: test@example.com')
            print('Password: password123')
        else:
            print('テストユーザーは既に存在します')
            print('Email: test@example.com')
            print('Password: password123')
            
    except Exception as e:
        print(f'エラー: {str(e)}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_test_user()