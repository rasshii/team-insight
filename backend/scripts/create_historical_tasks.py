#!/usr/bin/env python3
"""
過去のタスクデータを作成して生産性推移を可視化するためのスクリプト
"""

import os
import sys
import random
import requests
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_historical_tasks():
    """過去のタスクデータを作成"""
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
        "バックエンドAPI設計",
        "フロントエンド画面実装",
        "データベース設計",
        "認証機能実装",
        "ユニットテスト作成",
        "インテグレーションテスト",
        "パフォーマンスチューニング",
        "セキュリティ対策",
        "ドキュメント作成",
        "コードレビュー対応",
        "バグ修正",
        "新機能提案",
        "UI/UX改善",
        "インフラ構築",
        "CI/CD設定"
    ]
    
    # 過去6ヶ月分のタスクを作成
    created_count = 0
    now = datetime.now()
    
    for month_offset in range(6, 0, -1):  # 6ヶ月前から1ヶ月前まで
        month_start = now - timedelta(days=30 * month_offset)
        
        # 各月に10-20件のタスクを作成
        task_count_per_month = random.randint(10, 20)
        
        for _ in range(task_count_per_month):
            # ランダムにメンバーを選択
            member = random.choice(members)
            
            # タスクのタイトル
            task_title = f"{random.choice(task_templates)} - {member['name']} ({month_start.strftime('%Y年%m月')})"
            
            # 作成日をランダムに設定（その月内）
            created_date = month_start + timedelta(days=random.randint(0, 29))
            
            # 期限日を設定（作成日から1-14日後）
            due_date = created_date + timedelta(days=random.randint(1, 14))
            
            # タスクデータ
            task_data = {
                "projectId": backlog_project_id,
                "summary": task_title,
                "description": f"これは{member['name']}さんの{month_start.strftime('%Y年%m月')}のタスクです。\n\n過去データとして作成されました。",
                "issueTypeId": task_type_id,
                "priorityId": random.choice(priority_ids),
                "assigneeId": member['backlog_id'],
                "dueDate": due_date.strftime("%Y-%m-%d"),
                "createdDate": created_date.strftime("%Y-%m-%d")  # これは効かないかもしれない
            }
            
            try:
                # タスクを作成
                response = requests.post(f"{base_url}/issues", headers=headers, json=task_data)
                if response.status_code == 201:
                    result = response.json()
                    created_count += 1
                    issue_id = result['id']
                    print(f"作成済み: {task_title}")
                    
                    # 80%の確率で完了状態にする
                    if random.random() < 0.8:
                        # ステータスを完了に更新
                        update_data = {
                            "statusId": status_ids['closed']
                        }
                        update_response = requests.patch(
                            f"{base_url}/issues/{issue_id}",
                            headers=headers,
                            json=update_data
                        )
                        if update_response.status_code == 200:
                            print(f"  ステータス更新: 完了")
                            
                            # 実績時間を追加（2-16時間）
                            actual_hours = random.randint(2, 16)
                            completed_date = created_date + timedelta(days=random.randint(1, 10))
                            comment_data = {
                                "content": f"タスクを完了しました。実績時間: {actual_hours}時間\n完了日: {completed_date.strftime('%Y-%m-%d')}",
                                "actualHours": actual_hours
                            }
                            requests.post(
                                f"{base_url}/issues/{issue_id}/comments",
                                headers=headers,
                                json=comment_data
                            )
                        else:
                            print(f"  ステータス更新失敗: {update_response.text}")
                else:
                    print(f"タスク作成失敗: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"タスク作成エラー: {e}")
                continue
    
    print(f"\n合計 {created_count} 件の過去タスクを作成しました")

if __name__ == "__main__":
    create_historical_tasks()