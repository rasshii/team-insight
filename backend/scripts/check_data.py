#!/usr/bin/env python3
"""
データベース内のデータ数を確認するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_data():
    """データベース内のデータ数を確認"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # チーム数を確認
        result = conn.execute(text("SELECT COUNT(*) FROM team_insight.teams"))
        team_count = result.scalar()
        print(f"Teams: {team_count}")
        
        # タスク数を確認
        result = conn.execute(text("SELECT COUNT(*) FROM team_insight.tasks"))
        task_count = result.scalar()
        print(f"Tasks: {task_count}")
        
        # ユーザー数を確認
        result = conn.execute(text("SELECT COUNT(*) FROM team_insight.users"))
        user_count = result.scalar()
        print(f"Users: {user_count}")
        
        # プロジェクトメンバー数を確認
        result = conn.execute(text("SELECT COUNT(*) FROM team_insight.project_members"))
        project_member_count = result.scalar()
        print(f"Project Members: {project_member_count}")
        
        # プロジェクト数を確認
        result = conn.execute(text("SELECT COUNT(*) FROM team_insight.projects"))
        project_count = result.scalar()
        print(f"Projects: {project_count}")
        
        # 実際のプロジェクトのキーを確認
        if project_count > 0:
            result = conn.execute(text("SELECT id, project_key, name FROM team_insight.projects LIMIT 5"))
            print("\nProjects:")
            for row in result:
                print(f"  ID: {row[0]}, Key: {row[1]}, Name: {row[2]}")
        
        # 実際のユーザーを確認
        if user_count > 0:
            result = conn.execute(text("SELECT id, user_id, name FROM team_insight.users WHERE is_active = true LIMIT 5"))
            print("\nActive Users:")
            for row in result:
                print(f"  ID: {row[0]}, User ID: {row[1]}, Name: {row[2]}")

if __name__ == "__main__":
    check_data()