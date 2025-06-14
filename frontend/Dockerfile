FROM node:22-alpine AS builder

WORKDIR /app

# Yarnのセットアップ
RUN corepack enable && corepack prepare yarn@stable --activate

# 依存関係のインストール
COPY package.json yarn.lock ./
RUN yarn config set nodeLinker node-modules
RUN yarn install

# アプリケーションのビルド
COPY . .
RUN yarn build

# 本番環境用のイメージ
FROM node:22-alpine AS runner

WORKDIR /app

# 必要なファイルのみをコピー
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# アプリケーションの起動
CMD ["node", "server.js"]
