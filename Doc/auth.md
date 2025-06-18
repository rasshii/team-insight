# 認証フロー

## 概要

Team Insight は、Backlog の OAuth2.0 認証を使用してユーザー認証を行います。これにより、ユーザーは既存の Backlog アカウントで Team Insight にログインできます。

## 認証フロー

1. **ログインページ表示**

   - ユーザーが`/auth/login`にアクセス
   - ログインページが表示され、Backlog でログインボタンが表示される

2. **認証 URL 生成**

   - ユーザーが「Backlog でログイン」ボタンをクリック
   - フロントエンドから`/api/auth/backlog/authorize`にリクエスト
   - バックエンドで認証 URL と state を生成
   - 生成された認証 URL にリダイレクト

3. **Backlog 認証**

   - ユーザーが Backlog の認証ページで認証を承認
   - Backlog が`/auth/callback`にリダイレクト（認証コードと state を含む）

4. **コールバック処理**

   - バックエンドで認証コードをアクセストークンに交換
   - ユーザー情報を取得
   - ユーザーをデータベースに保存または更新
   - JWT トークンを生成
   - フロントエンドにトークンとユーザー情報を返却

5. **ダッシュボード表示**
   - フロントエンドでトークンを保存
   - ユーザーをダッシュボードにリダイレクト

## エンドポイント

### フロントエンド

- `/auth/login` - ログインページ
- `/auth/callback` - 認証コールバックページ

### バックエンド

- `GET /api/auth/backlog/authorize` - 認証 URL 生成
- `POST /api/auth/backlog/callback` - コールバック処理
- `POST /api/auth/backlog/refresh` - トークンリフレッシュ
- `GET /api/auth/me` - 現在のユーザー情報取得

## セキュリティ対策

1. **CSRF 対策**

   - 認証リクエスト時に state パラメータを生成
   - コールバック時に state パラメータを検証
   - state パラメータは 10 分間有効

2. **トークン管理**

   - アクセストークンは JWT 形式で発行
   - トークンは HttpOnly Cookie に保存
   - リフレッシュトークンはデータベースに保存

3. **エラーハンドリング**
   - 認証エラー時は適切なエラーメッセージを表示
   - トークン期限切れ時は自動的にリフレッシュ

## データベース

### OAuthState

認証リクエストの state を管理するテーブル

```sql
CREATE TABLE oauth_states (
    id SERIAL PRIMARY KEY,
    state VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### OAuthToken

Backlog のアクセストークンを管理するテーブル

```sql
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## フロントエンド実装

### 認証フック

`useAuth`フックを使用して認証状態を管理

```typescript
const { isAuthenticated, isInitialized, user } = useAuth();
```

### 認証状態に応じた表示

- 未認証: ランディングページ（LP）を表示
- 認証済み: ダッシュボードにリダイレクト

### 保護されたルート

`PrivateRoute`コンポーネントを使用して認証が必要なページを保護

```typescript
<PrivateRoute>
  <Layout>{/* 保護されたコンテンツ */}</Layout>
</PrivateRoute>
```

## エラーメッセージ

- 認証エラー: "認証に失敗しました"
- トークン期限切れ: "セッションの有効期限が切れました"
- リフレッシュエラー: "トークンの更新に失敗しました"
- サーバーエラー: "サーバーエラーが発生しました"
