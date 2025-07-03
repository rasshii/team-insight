#!/bin/bash

# Backlog認証のデバッグスクリプト

echo "=== Backlog認証のデバッグ情報 ==="
echo ""

echo "1. 現在の環境変数の確認:"
docker-compose exec backend bash -c "env | grep BACKLOG"
echo ""

echo "2. 最近の認証関連ログ:"
docker-compose logs backend | grep -E "(auth|callback|state)" | tail -20
echo ""

echo "3. Nginxのアクセスログ（認証関連）:"
docker-compose logs nginx | grep -E "(auth|callback)" | tail -10
echo ""

echo "4. データベースのOAuthState確認:"
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.auth import OAuthState
db = SessionLocal()
states = db.query(OAuthState).all()
print(f'OAuthState count: {len(states)}')
for state in states:
    print(f'- state: {state.state[:10]}..., expires_at: {state.expires_at}')
db.close()
"
echo ""

echo "5. 現在のコンテナ状態:"
docker-compose ps
echo ""

echo "=== デバッグ完了 ==="