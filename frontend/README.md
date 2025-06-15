# Team Insight Frontend

このプロジェクトは[Next.js](https://nextjs.org/)を使用して構築されています。

## 開発環境のセットアップ

必要なパッケージをインストールします：

```bash
yarn install
```

## 利用可能なスクリプト

プロジェクトディレクトリで以下のコマンドを実行できます：

### `yarn dev`

開発モードでアプリケーションを起動します。\
[http://localhost:3000](http://localhost:3000) でブラウザに表示されます。

コードの変更は自動的にリロードされます。\
コンソールに lint エラーが表示されます。

### `yarn build`

本番用にアプリケーションをビルドします。\
最適化された本番ビルドが`.next`フォルダに生成されます。

### `yarn start`

本番ビルドを実行します。\
`yarn build`を実行した後に使用してください。

### `yarn lint`

ESLint を使用してコードをリントします。

## プロジェクト構造

```
src/
  ├── app/          # アプリケーションのルーティングとレイアウト
  ├── components/   # 再利用可能なコンポーネント
  ├── lib/          # ユーティリティ関数や設定
  └── styles/       # グローバルスタイル
```

## 技術スタック

- [Next.js](https://nextjs.org/) - React フレームワーク
- [TypeScript](https://www.typescriptlang.org/) - 型安全な JavaScript
- [Tailwind CSS](https://tailwindcss.com/) - ユーティリティファーストの CSS フレームワーク
- [Redux Toolkit](https://redux-toolkit.js.org/) - 状態管理
