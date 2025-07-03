#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 '<callback-url>'"
    echo "Example: $0 'http://localhost/auth/callback?code=xxx&state=yyy'"
    exit 1
fi

CALLBACK_URL=$1

# URLからcodeとstateを抽出
CODE=$(echo "$CALLBACK_URL" | grep -o 'code=[^&]*' | cut -d= -f2)
STATE=$(echo "$CALLBACK_URL" | grep -o 'state=[^&]*' | cut -d= -f2)

echo "=== コールバック処理テスト ==="
echo "Code: $CODE"
echo "State: $STATE"
echo ""

# コールバックAPIを呼び出し
echo "コールバックAPIを呼び出し中..."
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -c auth_cookies.txt \
    -b auth_cookies.txt \
    -d "{\"code\":\"$CODE\",\"state\":\"$STATE\"}" \
    "http://localhost/api/v1/auth/backlog/callback")

echo "レスポンス:"
echo $response | jq
echo ""

# Cookieの確認
echo "=== 認証Cookie ==="
cat auth_cookies.txt | grep auth_token
echo ""

# 認証後のユーザー情報取得
echo "=== 認証後のユーザー情報 ==="
curl -s -b auth_cookies.txt "http://localhost/api/v1/auth/me" | jq

# クリーンアップ
rm -f auth_cookies.txt