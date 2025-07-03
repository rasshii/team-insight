#\!/bin/bash
echo "=== Current OAuth Configuration ==="
echo ""
echo "Backend:"
grep -E "BACKLOG_CLIENT_ID|BACKLOG_REDIRECT_URI|BACKLOG_SPACE_KEY" backend/.env | grep -v SECRET
echo ""
echo "Frontend:"  
grep -E "BACKLOG_" frontend/.env.local
echo ""
echo "=== Testing OAuth Flow ==="
curl -s http://localhost/api/v1/auth/backlog/authorize | jq
