#!/usr/bin/env python3
"""
管理者ログインとユーザー管理APIのテストスクリプト
"""

import requests
import json

base_url = "http://localhost"

# テスト用管理者アカウント情報（環境変数から設定されるはず）
admin_email = "admin@example.com"
admin_password = "AdminPassword123!"

def test_admin_login_and_users_api():
    """管理者でログインしてユーザー管理APIをテスト"""
    
    # セッションを使用してクッキーを保持
    session = requests.Session()
    
    # 1. ログイン
    print("1. 管理者アカウントでログイン...")
    login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    response = session.post(
        f"{base_url}/api/v1/auth/login",
        json=login_data
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ ログイン成功")
        user_data = response.json()
        print(f"   ユーザー情報: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
        
        # クッキーの確認
        print("\n   クッキー情報:")
        for cookie in session.cookies:
            print(f"   - {cookie.name}: {cookie.value[:20]}... (domain: {cookie.domain}, path: {cookie.path})")
    else:
        print(f"   ✗ ログイン失敗: {response.text}")
        return
    
    print()
    
    # 2. 現在のユーザー情報確認
    print("2. 現在のユーザー情報を確認...")
    response = session.get(f"{base_url}/api/v1/auth/me")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ 認証成功")
        current_user = response.json()
        print(f"   現在のユーザー: {current_user.get('email')}")
        print(f"   ロール: {[role['role']['name'] for role in current_user.get('user_roles', [])]}")
    else:
        print(f"   ✗ 認証失敗: {response.text}")
    
    print()
    
    # 3. 利用可能なロール一覧を取得
    print("3. 利用可能なロール一覧を取得...")
    response = session.get(f"{base_url}/api/v1/users/roles/available")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        roles = response.json()
        print("   ✓ 取得成功")
        for role in roles:
            print(f"   - {role['name']}: {role['description']}")
    else:
        print(f"   ✗ 取得失敗: {response.text}")
    
    print()
    
    # 4. ユーザー一覧を取得
    print("4. ユーザー一覧を取得...")
    params = {
        "page": 1,
        "per_page": 20,
        "sort_by": "created_at",
        "sort_order": "desc"
    }
    
    response = session.get(
        f"{base_url}/api/v1/users/",
        params=params
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   ✓ 取得成功")
        print(f"   総ユーザー数: {data.get('total', 0)}")
        print(f"   取得件数: {len(data.get('users', []))}")
        
        users = data.get('users', [])
        if users:
            print("\n   ユーザー一覧:")
            for user in users[:5]:  # 最初の5件のみ表示
                roles = [r['role']['name'] for r in user.get('user_roles', [])]
                print(f"   - {user['email']} (ID: {user['id']})")
                print(f"     名前: {user.get('name', 'N/A')}")
                print(f"     ロール: {', '.join(roles) if roles else 'なし'}")
                print(f"     アクティブ: {user['is_active']}")
                print(f"     メール確認済み: {user['is_email_verified']}")
    else:
        print(f"   ✗ 取得失敗: {response.text}")
    
    print()
    
    # 5. ログアウト
    print("5. ログアウト...")
    response = session.post(f"{base_url}/api/v1/auth/logout")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ ログアウト成功")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    test_admin_login_and_users_api()