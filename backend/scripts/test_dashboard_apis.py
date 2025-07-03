#!/usr/bin/env python3
"""
ダッシュボードAPI動作確認スクリプト

開発環境でダッシュボードAPIが正しく動作しているかテストします。
"""

import sys
import os
import requests
import json

# プロジェクトルートのパスをsys.pathに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_dashboard_apis():
    """ダッシュボードAPIのテスト"""
    
    base_url = "http://localhost:8000"
    
    # 1. ヘルスチェック
    print("1. ヘルスチェック...")
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {json.dumps(data, indent=2)}")
    print()
    
    # 2. 個人ダッシュボードAPI（認証なしでテスト）
    print("2. 個人ダッシュボードAPI（認証なし）...")
    response = requests.get(f"{base_url}/api/v1/analytics/personal/dashboard/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✓ 期待通り401エラー（認証が必要）")
    print()
    
    # 3. プロジェクトヘルスAPI（認証なしでテスト）
    print("3. プロジェクトヘルスAPI（認証なし）...")
    response = requests.get(f"{base_url}/api/v1/analytics/project/357/health/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✓ 期待通り401エラー（認証が必要）")
    print()
    
    # 4. データベース内のデータ確認
    print("4. データベース内のデータ確認...")
    from app.db.session import SessionLocal
    from app.models.task import Task
    from app.models.project import Project
    from app.models.user import User
    
    db = SessionLocal()
    try:
        projects = db.query(Project).count()
        users = db.query(User).count()
        tasks = db.query(Task).count()
        
        print(f"   プロジェクト数: {projects}")
        print(f"   ユーザー数: {users}")
        print(f"   タスク数: {tasks}")
        
        if tasks > 0:
            print("\n   ✅ サンプルデータが正常に作成されています！")
            print("   ブラウザでログイン後、以下のURLでダッシュボードを確認できます:")
            print("   - 個人ダッシュボード: http://localhost/dashboard/personal")
            print("   - プロジェクトダッシュボード: http://localhost/dashboard/project/357")
        else:
            print("\n   ⚠️  タスクデータがありません。")
            print("   scripts/create_sample_data.py を実行してサンプルデータを作成してください。")
            
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 ダッシュボードAPI動作確認を開始します...\n")
    test_dashboard_apis()
    print("\n✨ テスト完了！")