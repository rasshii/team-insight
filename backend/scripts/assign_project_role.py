#!/usr/bin/env python3
"""
プロジェクトロール割り当てスクリプト

使用例:
    python scripts/assign_project_role.py user@example.com 1 PROJECT_LEADER
    python scripts/assign_project_role.py user@example.com 2 MEMBER
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.models.rbac import Role, UserRole
from app.models.project import Project
from datetime import datetime


def get_db():
    """データベースセッション取得"""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def assign_project_role(email: str, project_id: int, role_name: str) -> None:
    """ユーザーにプロジェクトロールを割り当て"""
    db = get_db()
    try:
        # ロールの妥当性確認
        valid_roles = ["ADMIN", "PROJECT_LEADER", "MEMBER"]
        if role_name not in valid_roles:
            print(f"❌ 無効なロール: {role_name}")
            print(f"   有効なロール: {', '.join(valid_roles)}")
            return
        
        # ユーザーを取得
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ ユーザーが見つかりません: {email}")
            return
        
        # プロジェクトを取得
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            print(f"❌ プロジェクトが見つかりません: ID={project_id}")
            return
        
        # ロールを取得
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"❌ ロールが見つかりません: {role_name}")
            return
        
        # 既存の割り当てを確認
        existing = db.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == role.id,
            UserRole.project_id == project_id
        ).first()
        
        if existing:
            print(f"ℹ️  {email} は既にプロジェクト「{project.name}」で {role_name} ロールを持っています")
            return
        
        # プロジェクトロールを割り当て
        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
            project_id=project_id
        )
        db.add(user_role)
        db.commit()
        
        print(f"✅ {email} にプロジェクト「{project.name}」の {role_name} ロールを割り当てました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()


def list_project_roles(email: str = None) -> None:
    """プロジェクトロールの一覧表示"""
    db = get_db()
    try:
        query = db.query(UserRole).filter(UserRole.project_id.isnot(None))
        
        if email:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"❌ ユーザーが見つかりません: {email}")
                return
            query = query.filter(UserRole.user_id == user.id)
        
        user_roles = query.all()
        
        if not user_roles:
            print("プロジェクトロールの割り当てはありません")
            return
        
        print("\n🎯 プロジェクトロール一覧:")
        print("-" * 80)
        
        for ur in user_roles:
            project = db.query(Project).filter(Project.id == ur.project_id).first()
            project_name = project.name if project else f"不明 (ID: {ur.project_id})"
            print(f"ユーザー: {ur.user.email}")
            print(f"  プロジェクト: {project_name}")
            print(f"  ロール: {ur.role.name}")
            print(f"  説明: {ur.role.description or '説明なし'}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="プロジェクトロール管理ツール")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")
    
    # プロジェクトロール割り当てコマンド
    assign_parser = subparsers.add_parser("assign", help="プロジェクトロールを割り当て")
    assign_parser.add_argument("email", help="ユーザーのメールアドレス")
    assign_parser.add_argument("project_id", type=int, help="プロジェクトID")
    assign_parser.add_argument("role", help="ロール名 (ADMIN, PROJECT_LEADER, MEMBER)")
    
    # プロジェクトロール一覧コマンド
    list_parser = subparsers.add_parser("list", help="プロジェクトロール一覧を表示")
    list_parser.add_argument("-u", "--user", help="特定ユーザーのロールのみ表示")
    
    args = parser.parse_args()
    
    if args.command == "assign":
        assign_project_role(args.email, args.project_id, args.role)
    elif args.command == "list":
        list_project_roles(args.user)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()