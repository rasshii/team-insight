#!/usr/bin/env python3
"""
Backlog APIを使用してテストタスクを作成するシンプルなスクリプト
"""

import os
import sys
import random
import requests
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_test_tasks():
    """テストタスクを作成"""
    # データベース接続
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 管理者のトークンを取得（ADMINロールを持つユーザー）
        result = conn.execute(text("""
            SELECT ot.access_token 
            FROM team_insight.oauth_tokens ot
            JOIN team_insight.users u ON ot.user_id = u.id
            JOIN team_insight.user_roles ur ON u.id = ur.user_id
            JOIN team_insight.roles r ON ur.role_id = r.id
            WHERE r.name = 'ADMIN' AND ot.provider = 'backlog'
            LIMIT 1
        """))
        row = result.fetchone()
        if not row:
            print("管理者のBacklogトークンが見つかりません")
            return
        token = row[0]
        
        # プロジェクト情報を取得
        result = conn.execute(text("""
            SELECT id, project_key, name, backlog_id
            FROM team_insight.projects
            WHERE status = 'active'
            LIMIT 1
        """))
        project = result.fetchone()
        if not project:
            print("アクティブなプロジェクトが見つかりません")
            return
            
        project_id, project_key, project_name, backlog_project_id = project
        print(f"プロジェクト: {project_name} ({project_key})")
        
        # プロジェクトメンバーを取得
        result = conn.execute(text("""
            SELECT u.id, u.name, u.backlog_id
            FROM team_insight.users u
            JOIN team_insight.project_members pm ON u.id = pm.user_id
            WHERE pm.project_id = :project_id AND u.backlog_id IS NOT NULL
        """), {"project_id": project_id})
        
        members = []
        for row in result:
            members.append({
                'user_id': row[0],
                'name': row[1],
                'backlog_id': row[2]
            })
        
        print(f"メンバー数: {len(members)}")
        
        if not members:
            print("Backlog IDを持つメンバーが見つかりません")
            return
    
    # Backlog API基本設定
    base_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/api/v2"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # タスクタイプと優先度を取得
    try:
        # イシュータイプを取得
        response = requests.get(f"{base_url}/projects/{project_key}/issueTypes", headers=headers)
        issue_types = response.json()
        
        # 優先度を取得
        response = requests.get(f"{base_url}/priorities", headers=headers)
        priorities = response.json()
        
        # ステータスを取得
        response = requests.get(f"{base_url}/projects/{project_key}/statuses", headers=headers)
        statuses = response.json()
        
        # デフォルトのタスクタイプとステータスを設定
        task_type_id = issue_types[0]["id"] if issue_types else None
        priority_ids = [p["id"] for p in priorities] if priorities else [2]
        
        # ステータスIDを取得
        status_ids = {
            'todo': next((s["id"] for s in statuses if "未対応" in s["name"]), 1),
            'in_progress': next((s["id"] for s in statuses if "処理中" in s["name"]), 2),
            'resolved': next((s["id"] for s in statuses if "処理済み" in s["name"]), 3),
            'closed': next((s["id"] for s in statuses if "完了" in s["name"]), 4)
        }
        
        print(f"ステータスID: {status_ids}")
        
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
            
            # ランダムなステータスを選択（70%は完了系、30%は進行中）
            if random.random() < 0.7:
                status_choice = random.choice(['resolved', 'closed'])
            else:
                status_choice = random.choice(['todo', 'in_progress'])
            status_id = status_ids[status_choice]
            
            # 期限日を設定
            if status_choice in ['resolved', 'closed']:
                # 完了タスクは過去の日付
                due_date = datetime.now() - timedelta(days=random.randint(1, 30))
            else:
                # 進行中タスクは未来の日付
                due_date = datetime.now() + timedelta(days=random.randint(1, 30))
            
            # タスクデータ（statusIdは作成時に設定できない）
            task_data = {
                "projectId": backlog_project_id,
                "summary": task_title,
                "description": f"これは{member['name']}さんのテストタスクです。\n\n詳細な説明がここに入ります。",
                "issueTypeId": task_type_id,
                "priorityId": random.choice(priority_ids),
                "assigneeId": member['backlog_id'],
                "dueDate": due_date.strftime("%Y-%m-%d")
            }
            
            try:
                # タスクを作成
                response = requests.post(f"{base_url}/issues", headers=headers, json=task_data)
                if response.status_code == 201:
                    result = response.json()
                    created_count += 1
                    issue_id = result['id']
                    print(f"作成済み: {task_title} (担当: {member['name']})")
                    
                    # ステータスを更新（未対応以外の場合）
                    if status_choice != 'todo':
                        update_data = {
                            "statusId": status_id
                        }
                        update_response = requests.patch(
                            f"{base_url}/issues/{issue_id}",
                            headers=headers,
                            json=update_data
                        )
                        if update_response.status_code == 200:
                            print(f"  ステータス更新: {status_choice}")
                        else:
                            print(f"  ステータス更新失敗: {update_response.text}")
                    
                    # 完了タスクの場合は実績時間を設定
                    if status_choice in ['resolved', 'closed']:
                        # 実績時間を追加（1-8時間）
                        actual_hours = random.randint(1, 8)
                        comment_data = {
                            "content": f"タスクを完了しました。実績時間: {actual_hours}時間",
                            "actualHours": actual_hours
                        }
                        requests.post(
                            f"{base_url}/issues/{issue_id}/comments",
                            headers=headers,
                            json=comment_data
                        )
                else:
                    print(f"タスク作成失敗: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"タスク作成エラー: {e}")
                continue
    
    print(f"\n合計 {created_count} 件のタスクを作成しました")

if __name__ == "__main__":
    create_test_tasks()