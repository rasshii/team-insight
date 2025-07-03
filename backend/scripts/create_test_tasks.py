#!/usr/bin/env python3
"""
Backlog APIを使用してテストタスクを作成するスクリプト
"""

import sys
import os
import random
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.services.backlog_client import BacklogClient
from app.db.session import SessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken

def get_backlog_token():
    """管理者のBacklogトークンを取得"""
    db = SessionLocal()
    try:
        # 管理者ユーザーを取得
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if not admin_user:
            print("管理者ユーザーが見つかりません")
            return None
            
        # OAuthトークンを取得
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == admin_user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not token:
            print("Backlogトークンが見つかりません")
            return None
            
        return token.access_token
    finally:
        db.close()

def get_project_info():
    """プロジェクト情報とメンバー情報を取得"""
    db = SessionLocal()
    try:
        # アクティブなプロジェクトを取得
        project = db.query(Project).filter(Project.is_active == True).first()
        if not project:
            print("アクティブなプロジェクトが見つかりません")
            return None, []
            
        # プロジェクトメンバーを取得（多対多リレーション）
        backlog_users = []
        for user in project.members:
            if user.backlog_id:
                backlog_users.append({
                    'id': user.backlog_id,
                    'name': user.name
                })
        
        return project, backlog_users
    finally:
        db.close()

def create_test_tasks():
    """テストタスクを作成"""
    # Backlogトークンを取得
    token = get_backlog_token()
    if not token:
        return
        
    # プロジェクト情報を取得
    project, members = get_project_info()
    if not project or not members:
        print("プロジェクトまたはメンバーが見つかりません")
        return
        
    print(f"プロジェクト: {project.name} ({project.project_key})")
    print(f"メンバー数: {len(members)}")
    
    # BacklogClient初期化
    client = BacklogClient(
        space_key=settings.BACKLOG_SPACE_KEY,
        api_key=token
    )
    
    # タスクタイプと優先度を取得
    try:
        issue_types = client.get_issue_types(project.project_key)
        priorities = client.get_priorities()
        statuses = client.get_statuses(project.project_key)
        
        # デフォルトのタスクタイプとステータスを設定
        task_type_id = issue_types[0]["id"] if issue_types else None
        priority_ids = [p["id"] for p in priorities] if priorities else [2]
        
        # ステータスIDを取得（未対応、処理中、処理済み、完了）
        status_ids = {
            'todo': next((s["id"] for s in statuses if s["name"] == "未対応"), 1),
            'in_progress': next((s["id"] for s in statuses if s["name"] == "処理中"), 2),
            'resolved': next((s["id"] for s in statuses if s["name"] == "処理済み"), 3),
            'closed': next((s["id"] for s in statuses if s["name"] == "完了"), 4)
        }
        
    except Exception as e:
        print(f"プロジェクト設定の取得に失敗: {e}")
        return
    
    # タスクのサンプルデータ
    task_templates = [
        "ユーザー認証機能の実装",
        "APIエンドポイントの設計",
        "データベーススキーマの最適化",
        "フロントエンドコンポーネントの作成",
        "パフォーマンステストの実施",
        "セキュリティ監査の実施",
        "ドキュメントの更新",
        "バグ修正",
        "新機能の要件定義",
        "UIデザインの改善",
        "単体テストの作成",
        "統合テストの実施",
        "リファクタリング",
        "コードレビュー",
        "デプロイスクリプトの作成"
    ]
    
    # 各メンバーに対してタスクを作成
    created_count = 0
    for member in members:
        # 各メンバーに3-5個のタスクを作成
        task_count = random.randint(3, 5)
        
        for i in range(task_count):
            task_title = f"{random.choice(task_templates)} - {member['name']}"
            
            # ランダムなステータスを選択
            status_choice = random.choice(['todo', 'in_progress', 'resolved', 'closed'])
            status_id = status_ids[status_choice]
            
            # 期限日を設定（今日から30日以内）
            due_date = datetime.now() + timedelta(days=random.randint(1, 30))
            
            # タスクデータ
            task_data = {
                "projectId": project.backlog_project_id,
                "summary": task_title,
                "description": f"これは{member['name']}さんのテストタスクです。\n\n詳細な説明がここに入ります。",
                "issueTypeId": task_type_id,
                "priorityId": random.choice(priority_ids),
                "assigneeId": member['id'],
                "statusId": status_id,
                "dueDate": due_date.strftime("%Y-%m-%d")
            }
            
            try:
                # タスクを作成
                result = client._make_request("POST", "/api/v2/issues", data=task_data)
                created_count += 1
                print(f"作成済み: {task_title} (担当: {member['name']})")
                
                # 完了タスクの場合は実績時間を設定
                if status_choice in ['resolved', 'closed']:
                    # 実績時間を追加（1-8時間）
                    actual_hours = random.randint(1, 8)
                    comment_data = {
                        "content": f"タスクを完了しました。実績時間: {actual_hours}時間",
                        "actualHours": actual_hours
                    }
                    client._make_request(
                        "POST", 
                        f"/api/v2/issues/{result['id']}/comments",
                        data=comment_data
                    )
                    
            except Exception as e:
                print(f"タスク作成エラー: {e}")
                continue
    
    print(f"\n合計 {created_count} 件のタスクを作成しました")

if __name__ == "__main__":
    create_test_tasks()