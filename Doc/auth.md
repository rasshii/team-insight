# 認証システムの実装詳細

## 概要

このドキュメントでは、Team Insight アプリケーションの認証システムの実装詳細について説明します。
システムは Backlog OAuth2.0 を使用した認証フローを採用し、JWT トークンによるセッション管理を実装しています。

## 認証フロー

### 1. 認証開始

1. ユーザーが`/auth/login`にアクセス
2. フロントエンド（Next.js）が`/api/v1/auth/backlog/authorize`を呼び出し
3. バックエンド（FastAPI）が以下を生成：
   - Backlog 認証 URL
   - CSRF 対策用の state パラメータ
4. state をデータベースに保存（10 分間有効）
5. ユーザーを Backlog 認証ページにリダイレクト

### 2. 認証コールバック

1. Backlog 認証後、ユーザーが`/auth/callback`にリダイレクト
2. フロントエンドが`/api/v1/auth/backlog/callback`を呼び出し
3. バックエンドが以下を処理：
   - state パラメータの検証
   - 認証コードをアクセストークンに交換
   - ユーザー情報の取得
   - JWT トークンの生成
4. レスポンスに以下を含めて返却：
   - JWT トークン（JSON ボディ）
   - `auth_token`クッキー（Set-Cookie ヘッダー）

### 3. セッション管理

1. クライアント側：
   - JWT トークンを localStorage に保存
   - `auth_token`クッキーを自動的に送信
2. サーバー側：
   - Next.js の middleware で`auth_token`クッキーを検証
   - 保護されたルートへのアクセスを制御

## セキュリティ実装

### 1. CSRF 対策

- state パラメータの使用
- データベースでの state 管理
- 10 分間の有効期限設定

### 2. XSS 対策

- `HttpOnly`クッキーの使用
- `SameSite=Lax`の設定
- クライアント側での JWT トークン管理

### 3. トークン管理

- JWT トークンの有効期限設定（30 分）
- リフレッシュトークンの実装
- トークンの自動更新

## 環境変数設定

### フロントエンド（.env.local）

```env
# JWT認証用のシークレットキー
JWT_SECRET_KEY=your_secret_key_here

# APIのベースURL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### バックエンド（.env）

```env
# セキュリティ設定
SECRET_KEY=your_secret_key_here  # JWT_SECRET_KEYと同じ値

# データベース設定
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/team_insight

# Backlog OAuth2.0設定
BACKLOG_CLIENT_ID=your_client_id
BACKLOG_CLIENT_SECRET=your_client_secret
BACKLOG_REDIRECT_URI=http://localhost:3000/auth/callback
BACKLOG_SPACE_KEY=your_space_key

# CORS設定
BACKEND_CORS_ORIGINS=http://localhost:3000
```

## 主要なコンポーネント

### 1. フロントエンド

#### middleware.ts

```typescript
// 認証が必要なパス
const protectedPaths = ["/dashboard", "/projects", "/team"];

// JWTの検証関数
async function verifyAuthToken(token: string): Promise<boolean> {
  try {
    const secret = new TextEncoder().encode(
      process.env.JWT_SECRET_KEY || "your-secret-key-here"
    );
    await jwtVerify(token, secret);
    return true;
  } catch (error) {
    console.error("JWT検証エラー:", error);
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtectedPath = protectedPaths.some((path) =>
    pathname.startsWith(path)
  );

  if (isProtectedPath) {
    const authToken = request.cookies.get("auth_token")?.value;
    if (!authToken || !(await verifyAuthToken(authToken))) {
      return NextResponse.redirect(new URL("/auth/login", request.url));
    }
  }

  return NextResponse.next();
}
```

### 2. バックエンド

#### auth.py

```python
@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(request: CallbackRequest, db: Session = Depends(get_db)):
    # stateの検証
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == request.state
    ).first()

    if not oauth_state or oauth_state.is_expired():
        raise HTTPException(status_code=400, detail="無効なstateパラメータです")

    # 認証コードをアクセストークンに交換
    token_data = await backlog_oauth_service.exchange_code_for_token(request.code)

    # ユーザー情報を取得
    user_info = await backlog_oauth_service.get_user_info(token_data["access_token"])

    # ユーザーの作成または更新
    user = db.query(User).filter(User.backlog_id == user_info["id"]).first()
    if not user:
        user = User(
            backlog_id=user_info["id"],
            email=user_info.get("mailAddress"),
            name=user_info["name"],
            user_id=user_info["userId"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # JWTトークンを生成
    access_token = create_access_token(data={"sub": str(user.id)})

    # レスポンスを作成
    response = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserInfoResponse(
            id=user.id,
            backlog_id=user.backlog_id,
            email=user.email,
            name=user.name,
            user_id=user.user_id
        )
    )

    # Set-Cookieヘッダーを設定
    return JSONResponse(
        content=response.model_dump(),
        headers={
            "Set-Cookie": f"auth_token={access_token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800"
        }
    )
```

## エラーハンドリング

### 1. 認証エラー

- 無効な state パラメータ: 400 Bad Request
- トークン期限切れ: 401 Unauthorized
- 無効なトークン: 401 Unauthorized
- 権限不足: 403 Forbidden

### 2. エラーレスポンス形式

```json
{
  "detail": "エラーメッセージ",
  "status_code": 400
}
```

## 開発時の注意点

1. 環境変数の設定

   - 開発環境では`.env.example`の値を参考に設定
   - 本番環境では強力なシークレットキーを生成

2. セキュリティ設定

   - `JWT_SECRET_KEY`と`SECRET_KEY`は必ず同じ値を使用
   - 本番環境では`Secure`フラグを追加

3. CORS 設定
   - 開発環境: `http://localhost:3000`
   - 本番環境: 実際のドメインを設定

## トラブルシューティング

### 1. 認証エラーが発生する場合

1. クッキーが正しく設定されているか確認
2. JWT トークンが有効か確認
3. 環境変数が正しく設定されているか確認

### 2. リダイレクトループが発生する場合

1. middleware.ts の認証判定を確認
2. クッキーの設定を確認
3. 保護されたパスの設定を確認

### 3. CORS エラーが発生する場合

1. バックエンドの CORS 設定を確認
2. フロントエンドの API リクエスト設定を確認
3. クッキーの`SameSite`設定を確認
