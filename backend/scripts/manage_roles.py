#!/usr/bin/env python3
"""
ロール管理CLIツール

使用例:
    python scripts/manage_roles.py set-admin user@example.com
    python scripts/manage_roles.py set-role user@example.com PROJECT_LEADER
    python scripts/manage_roles.py list-users
    python scripts/manage_roles.py remove-role user@example.com PROJECT_LEADER
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.core.rbac import assign_role_to_user, remove_role_from_user
from datetime import datetime
from typing import Optional


def get_db():
    """データベースセッション取得"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def set_admin(email: str) -> None:
    """ユーザーを管理者に設定"""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ ユーザーが見つかりません: {email}")
            return
        
        # 既存のADMINロールを確認
        existing = db.query(UserRole).join(Role).filter(
            UserRole.user_id == user.id,
            Role.name == "ADMIN"
        ).first()
        
        if existing:
            print(f"ℹ️  {email} は既に管理者です")
            return
        
        # ADMINロールを付与
        assign_role_to_user(db, user.id, "ADMIN")
        print(f"✅ {email} を管理者に設定しました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


def set_role(email: str, role_name: str) -> None:
    """ユーザーにロールを設定"""
    db = get_db()
    try:
        # ロールの妥当性確認
        valid_roles = ["ADMIN", "PROJECT_LEADER", "MEMBER"]
        if role_name not in valid_roles:
            print(f"❌ 無効なロール: {role_name}")
            print(f"   有効なロール: {', '.join(valid_roles)}")
            return
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ ユーザーが見つかりません: {email}")
            return
        
        # 既存のロールを確認
        existing = db.query(UserRole).join(Role).filter(
            UserRole.user_id == user.id,
            Role.name == role_name
        ).first()
        
        if existing:
            print(f"ℹ️  {email} は既に {role_name} ロールを持っています")
            return
        
        # ロールを付与
        assign_role_to_user(db, user.id, role_name)
        print(f"✅ {email} に {role_name} ロールを設定しました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


def remove_role(email: str, role_name: str) -> None:
    """ユーザーからロールを削除"""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ ユーザーが見つかりません: {email}")
            return
        
        # ロールを削除
        removed = remove_role_from_user(db, user.id, role_name)
        if removed:
            print(f"✅ {email} から {role_name} ロールを削除しました")
        else:
            print(f"ℹ️  {email} は {role_name} ロールを持っていません")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


def list_users() -> None:
    """全ユーザーとロールを一覧表示"""
    db = get_db()
    try:
        users = db.query(User).all()
        
        if not users:
            print("ℹ️  ユーザーが登録されていません")
            return
        
        print("\n📋 ユーザー一覧:")
        print("-" * 80)
        print(f"{'Email':<30} {'名前':<20} {'ロール':<20} {'登録日':<20}")
        print("-" * 80)
        
        for user in users:
            # ユーザーのロールを取得
            user_roles = db.query(Role).join(UserRole).filter(
                UserRole.user_id == user.id
            ).all()
            
            roles_str = ", ".join([role.name for role in user_roles]) if user_roles else "なし"
            name = user.display_name or "未設定"
            created = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "不明"
            
            print(f"{user.email:<30} {name:<20} {roles_str:<20} {created:<20}")
        
        print("-" * 80)
        print(f"合計: {len(users)} ユーザー\n")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
    finally:
        db.close()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="Team Insight ロール管理ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/manage_roles.py set-admin user@example.com
  python scripts/manage_roles.py set-role user@example.com PROJECT_LEADER
  python scripts/manage_roles.py list-users
  python scripts/manage_roles.py remove-role user@example.com PROJECT_LEADER
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")
    
    # set-adminコマンド
    admin_parser = subparsers.add_parser("set-admin", help="ユーザーを管理者に設定")
    admin_parser.add_argument("email", help="対象ユーザーのメールアドレス")
    
    # set-roleコマンド
    role_parser = subparsers.add_parser("set-role", help="ユーザーにロールを設定")
    role_parser.add_argument("email", help="対象ユーザーのメールアドレス")
    role_parser.add_argument("role", help="設定するロール (ADMIN, PROJECT_LEADER, MEMBER)")
    
    # remove-roleコマンド
    remove_parser = subparsers.add_parser("remove-role", help="ユーザーからロールを削除")
    remove_parser.add_argument("email", help="対象ユーザーのメールアドレス")
    remove_parser.add_argument("role", help="削除するロール")
    
    # list-usersコマンド
    list_parser = subparsers.add_parser("list-users", help="全ユーザーとロールを一覧表示")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # コマンド実行
    if args.command == "set-admin":
        set_admin(args.email)
    elif args.command == "set-role":
        set_role(args.email, args.role)
    elif args.command == "remove-role":
        remove_role(args.email, args.role)
    elif args.command == "list-users":
        list_users()


if __name__ == "__main__":
    main()