# Backlog OAuth設定ガイド

## アプリケーション設定

Team InsightはBacklog OAuth 2.0を使用して認証を行います。以下の設定が必要です：

### Backlog側の設定

1. Backlogにログインし、個人設定 → アプリケーションにアクセス
2. 「新しいアプリケーションを追加」をクリック
3. 以下の情報を入力：

| 項目 | 値 |
|------|-----|
| アプリケーション名 | Team Insight |
| アプリケーションの説明 | チーム生産性分析ツール |
| リダイレクトURI | `http://localhost/auth/callback` |

⚠️ **重要な注意事項**:
- リダイレクトURIは**Nginxリバースプロキシ経由**のURLを使用
- 直接アクセス（`http://localhost:3000`）ではなく、`http://localhost`を使用
- URLの末尾にスラッシュを付けない

### 環境変数の設定

アプリケーション作成後、以下の情報を環境変数に設定：

**Backend (.env)**:
```bash
BACKLOG_CLIENT_ID=<発行されたクライアントID>
BACKLOG_CLIENT_SECRET=<発行されたクライアントシークレット>
BACKLOG_REDIRECT_URI=http://localhost/auth/callback
BACKLOG_SPACE_KEY=<あなたのスペースキー>
```

**Frontend (.env.local)**:
```bash
NEXT_PUBLIC_BACKLOG_CLIENT_ID=<発行されたクライアントID>
NEXT_PUBLIC_BACKLOG_REDIRECT_URI=http://localhost/auth/callback
```

### トラブルシューティング

#### 404エラーが発生する場合

1. リダイレクトURIが正確に一致しているか確認
2. アプリケーションが有効になっているか確認
3. クライアントIDが正しいか確認

#### 認証後にリダイレクトされない場合

1. Nginxが正しく起動しているか確認: `docker-compose ps nginx`
2. ブラウザの開発者ツールでネットワークタブを確認
3. Cookieが正しく設定されているか確認

### 開発環境と本番環境の切り替え

開発環境と本番環境で異なるリダイレクトURIを使用する場合は、Backlogで複数のアプリケーションを作成するか、環境に応じて設定を切り替えてください。

```bash
# 開発環境
BACKLOG_REDIRECT_URI=http://localhost/auth/callback

# 本番環境（例）
BACKLOG_REDIRECT_URI=https://teaminsight.example.com/auth/callback
```