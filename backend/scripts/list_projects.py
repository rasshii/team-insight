#!/usr/bin/env python3
"""
プロジェクト一覧確認スクリプト
"""
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.project import Project


def list_projects():
    """プロジェクト一覧を表示"""
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.id).all()
        
        if not projects:
            print("プロジェクトが登録されていません")
            print("\nプロジェクトを同期するには以下を実行してください:")
            print("1. Backlogへログイン")
            print("2. プロジェクト一覧ページで「プロジェクトを同期」ボタンをクリック")
            return
        
        print(f"\n📊 登録プロジェクト一覧 (合計: {len(projects)}件)")
        print("=" * 100)
        print(f"{'ID':<10} {'Backlog ID':<15} {'プロジェクト名':<30} {'メンバー数':<10} {'作成日':<20}")
        print("-" * 100)
        
        for project in projects:
            member_count = len(project.members) if project.members else 0
            created_at = project.created_at.strftime("%Y-%m-%d %H:%M") if project.created_at else "不明"
            
            print(f"{project.id:<10} {project.backlog_id or 'なし':<15} {project.name[:30]:<30} {member_count:<10} {created_at:<20}")
        
        # ID 357のプロジェクトを確認
        project_357 = db.query(Project).filter(Project.id == 357).first()
        if project_357:
            print(f"\n✅ プロジェクトID 357 は存在します: {project_357.name}")
        else:
            print("\n❌ プロジェクトID 357 は存在しません")
            
            # 最大IDを表示
            max_id = db.query(Project).order_by(Project.id.desc()).first()
            if max_id:
                print(f"   現在の最大プロジェクトID: {max_id.id}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    list_projects()