#!/bin/bash

# スクリプトの使用方法を表示
show_usage() {
    echo "Usage: $0 [nginx|direct]"
    echo ""
    echo "  nginx  - Use Nginx reverse proxy (http://localhost/auth/callback)"
    echo "  direct - Use direct access (http://localhost:3000/auth/callback)"
    echo ""
    exit 1
}

# 引数チェック
if [ $# -ne 1 ]; then
    show_usage
fi

MODE=$1

case $MODE in
    nginx)
        echo "Switching to Nginx reverse proxy mode..."
        REDIRECT_URI="http://localhost/auth/callback"
        ;;
    direct)
        echo "Switching to direct access mode..."
        REDIRECT_URI="http://localhost:3000/auth/callback"
        ;;
    *)
        show_usage
        ;;
esac

echo "Setting REDIRECT_URI to: $REDIRECT_URI"
echo ""

# Backend .env
echo "Updating backend/.env..."
sed -i.bak "s|BACKLOG_REDIRECT_URI=.*|BACKLOG_REDIRECT_URI=$REDIRECT_URI|" backend/.env

# Frontend .env.local
echo "Updating frontend/.env.local..."
sed -i.bak "s|NEXT_PUBLIC_BACKLOG_REDIRECT_URI=.*|NEXT_PUBLIC_BACKLOG_REDIRECT_URI=$REDIRECT_URI|" frontend/.env.local

echo ""
echo "Configuration updated!"
echo "Please restart services with: make restart"
echo ""
echo "Don't forget to update the redirect URI in Backlog application settings to: $REDIRECT_URI"