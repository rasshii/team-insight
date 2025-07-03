#!/bin/bash

echo "=== Team Insight認証フローテスト ==="
echo ""

# 1. 認証URL取得
echo "1. 認証URLを取得..."
response=$(curl -s -c cookies.txt "http://localhost/api/v1/auth/backlog/authorize")
auth_url=$(echo $response | jq -r '.authorization_url')
state=$(echo $response | jq -r '.state')

echo "Authorization URL: $auth_url"
echo "State: $state"
echo ""

# 2. Cookieの確認
echo "2. Cookieの確認..."
echo "=== 保存されたCookie ==="
cat cookies.txt
echo ""

# 3. 現在のユーザー情報取得（認証前）
echo "3. 認証前のユーザー情報取得..."
curl -s -b cookies.txt "http://localhost/api/v1/auth/me" | jq
echo ""

echo "=== 次のステップ ==="
echo "1. ブラウザで以下のURLにアクセス:"
echo "   $auth_url"
echo ""
echo "2. Backlogで認証を許可"
echo ""
echo "3. リダイレクト後のURLをコピーして、以下のコマンドを実行:"
echo "   ./scripts/test-callback.sh '<リダイレクトされたURL>'"

# クリーンアップ
rm -f cookies.txt