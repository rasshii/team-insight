FROM node:22-alpine

WORKDIR /app

# yarnをインストール（Node.js 22にはyarnが含まれていない場合があるため）
RUN corepack enable && corepack prepare yarn@stable --activate

# package.jsonとyarn.lockをコピー
COPY package.json yarn.lock ./

# Yarn PnPを無効にしてnode_modulesモードを使用
RUN yarn config set nodeLinker node-modules

# 依存関係をインストール
RUN yarn install

# アプリケーションのソースコードをコピー
COPY . .

EXPOSE 3000

CMD ["yarn", "start"]
