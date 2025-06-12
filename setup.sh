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

# データベースが起動するまで待機
echo -e "\n${YELLOW}⏳ データベースの起動を待っています...${NC}"
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅ データベースが起動しました${NC}"
        break
    fi
    echo -n "."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}❌ データベースの起動がタイムアウトしました${NC}"
    exit 1
fi

# データベースマイグレーションの実行
echo -e "\n${YELLOW}🗃️  データベースマイグレーションを実行しています...${NC}"
docker-compose exec -T backend alembic upgrade head
echo -e "${GREEN}✅ マイグレーションが完了しました${NC}"

# サービスの状態確認
echo -e "\n${YELLOW}📊 サービスの状態を確認しています...${NC}"
docker-compose ps

echo -e "\n${GREEN}✅ セットアップが完了しました！${NC}"
echo -e "\n${BLUE}アクセスURL:${NC}"
echo -e "  - フロントエンド: ${GREEN}http://localhost:3000${NC}"
echo -e "  - バックエンドAPI: ${GREEN}http://localhost:8000${NC}"
echo -e "  - APIドキュメント: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}💡 ヒント:${NC}"
echo -e "  - ログを確認: ${BLUE}make logs${NC}"
echo -e "  - サービス停止: ${BLUE}make stop${NC}"
echo -e "  - サービス再起動: ${BLUE}make restart${NC}"
