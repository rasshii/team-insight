#!/bin/bash

# Team Insight 開発環境セットアップスクリプト

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║       Team Insight Setup Script      ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# 必要なコマンドの確認
echo -e "${YELLOW}🔍 必要なコマンドを確認しています...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Dockerがインストールされていません${NC}"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Composeがインストールされていません${NC}"
    echo "https://docs.docker.com/compose/install/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Dockerが起動していません${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 必要なコマンドが確認できました${NC}"

# 環境変数ファイルの作成
echo -e "\n${YELLOW}📝 環境変数ファイルを作成しています...${NC}"

if [ ! -f frontend/.env ]; then
    cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✅ frontend/.env を作成しました${NC}"
fi

if [ ! -f backend/.env ]; then
    cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/team_insight
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-here
DEBUG=True
EOF
    echo -e "${GREEN}✅ backend/.env を作成しました${NC}"
fi

# Docker環境を構築
echo -e "\n${YELLOW}🚀 Docker環境を構築しています...${NC}"
docker-compose build
docker-compose up -d

echo -e "\n${GREEN}✅ セットアップが完了しました！${NC}"
