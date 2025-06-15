# ビルドステージ
FROM node:20-alpine AS builder

# 作業ディレクトリの設定
WORKDIR /app

# 必要なパッケージのインストール
RUN apk add --no-cache python3 make g++

# パッケージマネージャーの設定
COPY package.json yarn.lock ./

# 依存関係のインストール
RUN yarn install --frozen-lockfile --network-timeout 100000

# アプリケーションのコピー
COPY . .

# 環境変数の設定
ENV NEXT_TELEMETRY_DISABLED=1

# ビルド
RUN yarn build

# 実行ステージ
FROM node:20-alpine AS runner

WORKDIR /app

# 必要なパッケージのインストール
RUN apk add --no-cache python3 make g++

# グループとユーザーの作成
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# 必要なファイルのコピー
COPY --from=builder /app/package.json ./
COPY --from=builder /app/yarn.lock ./
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# 依存関係のインストール（本番用）
RUN yarn install --production --frozen-lockfile --network-timeout 100000

# ユーザーの切り替え
USER nextjs

# ポートの公開
EXPOSE 3000

# 環境変数の設定
ENV PORT 3000
ENV NODE_ENV production

# アプリケーションの起動
CMD ["node", "server.js"]
