#!/usr/bin/env python3
"""
RBAC統合テストスクリプト

このスクリプトは、認証APIがロール情報を正しく返すことを確認します。
"""

import requests
import json
import sys
import os
from typing import Dict, Optional

# APIのベースURL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def print_header(title: str):
    """ヘッダーを表示"""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)


def print_json(data: Dict, indent: int = 2):
    """JSONデータを整形して表示"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def test_auth_me_endpoint(token: str):
    """
    /api/v1/auth/meエンドポイントをテスト
    """
    print_header("Testing /api/v1/auth/me")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/v1/auth/me", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nUser Info:")
        print(f"- ID: {data.get('id')}")
        print(f"- Name: {data.get('name')}")
        print(f"- Email: {data.get('email')}")
        print(f"- Backlog ID: {data.get('backlog_id')}")
        
        print("\nUser Roles:")
        user_roles = data.get('user_roles', [])
        if user_roles:
            for user_role in user_roles:
                role = user_role.get('role', {})
                project_id = user_role.get('project_id')
                scope = f"Project {project_id}" if project_id else "Global"
                print(f"- {role.get('name')} ({scope}): {role.get('description')}")
        else:
            print("- No roles assigned")
        
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_verify_endpoint(token: str):
    """
    /api/v1/auth/verifyエンドポイントをテスト
    """
    print_header("Testing /api/v1/auth/verify")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/v1/auth/verify", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nVerified User:")
        print_json(data)
        return True
    else:
        print(f"Error: {response.text}")
        return False


def test_users_endpoint(token: str):
    """
    /api/v1/users エンドポイントをテスト（管理者のみ）
    """
    print_header("Testing /api/v1/users (Admin Only)")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/v1/users", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Users: {data.get('total')}")
        print(f"Page: {data.get('page')} / Per Page: {data.get('per_page')}")
        
        users = data.get('users', [])
        if users:
            print("\nFirst User:")
            print_json(users[0])
        return True
    elif response.status_code == 403:
        print("Access Denied: Admin role required")
        return True  # This is expected for non-admin users
    else:
        print(f"Error: {response.text}")
        return False


def test_available_roles(token: str):
    """
    利用可能なロール一覧を取得
    """
    print_header("Testing /api/v1/users/roles/available")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/v1/users/roles/available", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        roles = response.json()
        print("\nAvailable Roles:")
        for role in roles:
            print(f"- {role['name']} (ID: {role['id']}): {role['description']}")
        return True
    elif response.status_code == 403:
        print("Access Denied: Admin role required")
        return True
    else:
        print(f"Error: {response.text}")
        return False


def main():
    """
    メイン処理
    """
    print("RBAC Integration Test Script")
    print("============================")
    
    # 環境変数からトークンを取得（テスト用）
    token = os.getenv("AUTH_TOKEN")
    
    if not token:
        print("\nPlease set AUTH_TOKEN environment variable with a valid JWT token.")
        print("You can get a token by logging in through the web interface.")
        sys.exit(1)
    
    # 各エンドポイントをテスト
    tests_passed = 0
    total_tests = 4
    
    if test_auth_me_endpoint(token):
        tests_passed += 1
    
    if test_verify_endpoint(token):
        tests_passed += 1
    
    if test_users_endpoint(token):
        tests_passed += 1
    
    if test_available_roles(token):
        tests_passed += 1
    
    # 結果のサマリー
    print_header("Test Summary")
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())