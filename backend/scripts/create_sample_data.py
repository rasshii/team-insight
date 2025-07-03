#!/usr/bin/env python3
"""
サンプルデータ作成スクリプト

開発環境でダッシュボードのテスト用にサンプルタスクデータを作成します。
"""

import sys
import os
from datetime import datetime, timedelta
import random

# プロジェクトルートのパスをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.models.project import Project
# Import SyncHistory to resolve the relationship
from app.models.sync_history import SyncHistory

def create_sample_tasks(db: Session):
    """サンプルタスクを作成"""
    
    # 既存のプロジェクトとユーザーを取得
    project = db.query(Project).first()
    user = db.query(User).first()
    
    if not project:
        print("Error: プロジェクトが存在しません。先にプロジェクトを作成してください。")
        return
    
    if not user:
        print("Error: ユーザーが存在しません。先にユーザーを作成してください。")
        return
    
    print(f"プロジェクト '{project.name}' (ID: {project.id}) にサンプルタスクを作成します...")
    print(f"担当者: '{user.name}' (ID: {user.id})")
    
    # 既存のタスク数を確認
    existing_tasks = db.query(Task).filter(Task.project_id == project.id).count()
    print(f"既存のタスク数: {existing_tasks}")
    
    # タスクのサンプルデータ
    task_templates = [
        # 完了済みタスク（過去30日間に分散）
        {"title": "ユーザー認証機能の実装", "status": TaskStatus.CLOSED, "priority": TaskPriority.HIGH, "issue_type": "機能"},
        {"title": "ダッシュボードUIの改善", "status": TaskStatus.CLOSED, "priority": TaskPriority.MEDIUM, "issue_type": "改善"},
        {"title": "ログインエラーの修正", "status": TaskStatus.CLOSED, "priority": TaskPriority.HIGH, "issue_type": "バグ"},
        {"title": "パフォーマンスの最適化", "status": TaskStatus.CLOSED, "priority": TaskPriority.MEDIUM, "issue_type": "改善"},
        {"title": "APIドキュメントの更新", "status": TaskStatus.CLOSED, "priority": TaskPriority.LOW, "issue_type": "タスク"},
        {"title": "単体テストの追加", "status": TaskStatus.CLOSED, "priority": TaskPriority.MEDIUM, "issue_type": "タスク"},
        {"title": "データベーススキーマの設計", "status": TaskStatus.CLOSED, "priority": TaskPriority.HIGH, "issue_type": "機能"},
        {"title": "エラーハンドリングの改善", "status": TaskStatus.CLOSED, "priority": TaskPriority.MEDIUM, "issue_type": "改善"},
        {"title": "CI/CDパイプラインの構築", "status": TaskStatus.CLOSED, "priority": TaskPriority.HIGH, "issue_type": "機能"},
        {"title": "セキュリティ脆弱性の修正", "status": TaskStatus.CLOSED, "priority": TaskPriority.HIGH, "issue_type": "バグ"},
        
        # 進行中のタスク
        {"title": "レポート機能の開発", "status": TaskStatus.IN_PROGRESS, "priority": TaskPriority.HIGH, "issue_type": "機能"},
        {"title": "通知システムの実装", "status": TaskStatus.IN_PROGRESS, "priority": TaskPriority.MEDIUM, "issue_type": "機能"},
        {"title": "UIレスポンシブ対応", "status": TaskStatus.IN_PROGRESS, "priority": TaskPriority.MEDIUM, "issue_type": "改善"},
        {"title": "メモリリークの調査", "status": TaskStatus.IN_PROGRESS, "priority": TaskPriority.HIGH, "issue_type": "バグ"},
        
        # 未着手のタスク
        {"title": "ダークモードの実装", "status": TaskStatus.TODO, "priority": TaskPriority.LOW, "issue_type": "機能"},
        {"title": "多言語対応", "status": TaskStatus.TODO, "priority": TaskPriority.MEDIUM, "issue_type": "機能"},
        {"title": "バックアップ機能の追加", "status": TaskStatus.TODO, "priority": TaskPriority.HIGH, "issue_type": "機能"},
        {"title": "ユーザーガイドの作成", "status": TaskStatus.TODO, "priority": TaskPriority.LOW, "issue_type": "タスク"},
        {"title": "パフォーマンステストの実施", "status": TaskStatus.TODO, "priority": TaskPriority.MEDIUM, "issue_type": "タスク"},
        {"title": "APIレート制限の実装", "status": TaskStatus.TODO, "priority": TaskPriority.MEDIUM, "issue_type": "機能"},
        
        # 期限切れのタスク（要注意）
        {"title": "緊急セキュリティパッチ", "status": TaskStatus.TODO, "priority": TaskPriority.HIGH, "issue_type": "バグ", "overdue": True},
        {"title": "データ移行スクリプトの作成", "status": TaskStatus.IN_PROGRESS, "priority": TaskPriority.HIGH, "issue_type": "タスク", "overdue": True},
    ]
    
    created_tasks = []
    now = datetime.now()
    
    for i, template in enumerate(task_templates):
        # タスクの基本情報
        task = Task(
            backlog_id=1000 + i,  # ダミーのBacklog ID
            backlog_key=f"TEST-{1000 + i}",  # ダミーのBacklogキー
            project_id=project.id,
            assignee_id=user.id,
            reporter_id=user.id,
            title=template["title"],
            description=f"{template['title']}の詳細説明です。このタスクは開発環境のテスト用サンプルデータです。",
            status=template["status"],
            priority=template["priority"].value,  # Enumの値を取得
            issue_type_name=template["issue_type"]
        )
        
        # 作成日時を過去に設定（ランダムに分散）
        days_ago = random.randint(1, 45)
        task.created_at = now - timedelta(days=days_ago)
        task.updated_at = task.created_at + timedelta(hours=random.randint(1, 48))
        
        # 期限の設定
        if template.get("overdue"):
            # 期限切れタスク
            task.due_date = now - timedelta(days=random.randint(1, 7))
        else:
            # 通常のタスク（未来の期限）
            task.due_date = now + timedelta(days=random.randint(3, 30))
        
        # 完了タスクの場合
        if task.status == TaskStatus.CLOSED:
            # 完了日を設定（作成から数日後）
            completion_days = random.randint(1, 14)
            task.completed_date = task.created_at + timedelta(days=completion_days)
            task.updated_at = task.completed_date
        
        # ステータスが進行中の場合、更新日を最近に
        if task.status == TaskStatus.IN_PROGRESS:
            task.updated_at = now - timedelta(days=random.randint(0, 3))
        
        db.add(task)
        created_tasks.append(task)
    
    # データベースにコミット
    try:
        db.commit()
        print(f"\n✅ {len(created_tasks)}件のサンプルタスクを作成しました！")
        
        # 統計情報を表示
        print("\n📊 タスク統計:")
        print(f"  - 完了: {len([t for t in created_tasks if t.status == TaskStatus.CLOSED])}件")
        print(f"  - 進行中: {len([t for t in created_tasks if t.status == TaskStatus.IN_PROGRESS])}件")
        print(f"  - 未着手: {len([t for t in created_tasks if t.status == TaskStatus.TODO])}件")
        print(f"  - 期限切れ: {len([t for t in created_tasks if t.due_date and t.due_date < now and t.status != TaskStatus.CLOSED])}件")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ エラーが発生しました: {str(e)}")
        raise

def main():
    """メイン処理"""
    print("🚀 サンプルデータ作成スクリプトを開始します...")
    
    db = SessionLocal()
    try:
        create_sample_tasks(db)
        print("\n✨ サンプルデータの作成が完了しました！")
        print("ブラウザでダッシュボードを確認してください:")
        print("  - 個人ダッシュボード: http://localhost/dashboard/personal")
        print("  - プロジェクトダッシュボード: http://localhost/dashboard/project/357")
    finally:
        db.close()

if __name__ == "__main__":
    main()