#!/usr/bin/env python3
"""
プロジェクトロールの確認スクリプト
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
from app.models.project import Project


def check_project_roles():
    """プロジェクトロールの確認"""
    db = SessionLocal()
    try:
        # プロジェクトロールを持つユーザーを検索
        user_roles = db.query(UserRole).filter(
            UserRole.project_id.isnot(None)
        ).all()
        
        if not user_roles:
            print("プロジェクトロールを持つユーザーはいません")
            print("\n使用例:")
            print("python scripts/assign_project_role.py assign user@example.com 1 PROJECT_LEADER")
            return
        
        print(f"\n📊 プロジェクトロール一覧 (合計: {len(user_roles)}件)")
        print("=" * 100)
        print(f"{'ユーザー':<30} {'ロール':<15} {'プロジェクトID':<15} {'プロジェクト名':<30}")
        print("-" * 100)
        
        for ur in user_roles:
            project = db.query(Project).filter(Project.id == ur.project_id).first()
            project_name = project.name if project else "不明"
            user_email = ur.user.email or "メールなし"
            
            print(f"{user_email:<30} {ur.role.name:<15} {ur.project_id:<15} {project_name:<30}")
        
        # グローバルロールも表示
        global_roles = db.query(UserRole).filter(
            UserRole.project_id.is_(None)
        ).all()
        
        if global_roles:
            print(f"\n\n📊 グローバルロール一覧 (合計: {len(global_roles)}件)")
            print("=" * 100)
            print(f"{'ユーザー':<30} {'ロール':<15} {'説明':<50}")
            print("-" * 100)
            
            for ur in global_roles:
                user_email = ur.user.email or "メールなし"
                description = ur.role.description or "説明なし"
                print(f"{user_email:<30} {ur.role.name:<15} {description:<50}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_project_roles()