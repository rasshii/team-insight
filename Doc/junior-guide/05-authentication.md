# 認証システムの詳細

**このガイドで学べること**：
- 認証と認可の基本概念から実装まで
- OAuth 2.0の仕組みをステップバイステップで理解
- JWTトークンの基礎から実装方法
- RBAC（ロールベースアクセス制御）の完全理解
- セキュリティのベストプラクティス

## 🌟 はじめに：認証と認可の基本

### 認証（Authentication）と認可（Authorization）の違い

多くの人が混同しやすい概念です：

- **認証（Authentication）**: 「あなたは誰ですか？」
  - ユーザーの身元を確認するプロセス
  - 例：ログイン（メール/パスワード、指紋、顔認証など）

- **認可（Authorization）**: 「何をする権限がありますか？」
  - 認証されたユーザーが何をできるかを決定
  - 例：管理者のみがユーザーを削除できる

```
認証 → 誰であるかを確認
認可 → 何ができるかを確認
```

### なぜOAuth 2.0を使うのか？

#### 🏠 日常生活で例えると

**従来の方法（パスワードを渡す）**：
```
あなた：「荷物を受け取ってもらいたいので、家の鍵を渡します」
Team Insight：「分かりました。でも鍵があれば家の中全部にアクセスできちゃいますよ？」

リスク：
- 鍵（パスワード）を紛失される可能性
- 必要以上の場所にアクセスされる可能性
- 鍵を返してもらえない可能性
```

**OAuth 2.0の方法（一時的な許可証）**：
```
あなた：「宅配ボックスの一時パスコードを発行します」
Team Insight：「このパスコードで荷物だけ受け取れます」
Backlog：「パスコードは1時間で無効になります」

メリット：
- 限定的なアクセス（荷物の受け取りのみ）
- 時間制限あり（自動的に無効化）
- いつでも取り消し可能
```

#### 🔧 技術的な説明

**従来の方法の問題点**：
```
ユーザー → Team Insight → Backlog API
         ↑
    Backlogのパスワードを預ける必要がある！（危険）
    
問題：
1. Team InsightがBacklogパスワードを保存する必要がある
2. Team Insightがハッキングされたらパスワードが漏洩
3. ユーザーはTeam Insightを100%信頼する必要がある
```

**OAuth 2.0を使った方法**：
```
ユーザー → Backlog（直接ログイン）
         ↓
      認可コード（一時的）
         ↓
    Team Insight → Backlog API（アクセストークンで通信）
    
利点：
1. Team InsightはBacklogパスワードを知らない
2. アクセストークンは期限付き＆権限限定
3. ユーザーはBacklogの画面でいつでも連携解除可能
```

## 🔐 認証システムの概要

Team Insightの認証システムは以下の3つの要素で構成されています：

1. **Backlog OAuth 2.0**: ユーザー認証（誰であるかを確認）
2. **JWT (HttpOnly Cookie)**: セッション管理（ログイン状態の維持）
3. **RBAC**: 権限管理（何ができるかを制御）

### 認証システムのアーキテクチャ図

```mermaid
graph TB
    subgraph User["ユーザー"]
        Browser["ブラウザ"]
    end
    
    subgraph Frontend["フロントエンド"]
        LoginPage["ログインページ"]
        Dashboard["ダッシュボード"]
        AuthMiddleware["認証ミドルウェア"]
    end
    
    subgraph Backend["バックエンド"]
        AuthAPI["認証API"]
        AuthService["認証サービス"]
        JWTHandler["JWTハンドラー"]
        RBACChecker["RBACチェッカー"]
    end
    
    subgraph External["外部サービス"]
        BacklogOAuth["Backlog OAuth"]
        BacklogAPI["Backlog API"]
    end
    
    subgraph Storage["ストレージ"]
        DB["PostgreSQL"]
        Redis["Redis"]
    end
    
    Browser -->|"ログインボタン"| LoginPage
    LoginPage -->|"/auth/backlog/authorize"| AuthAPI
    AuthAPI -->|"state生成"| AuthService
    AuthService -->|"state保存"| DB
    AuthService -->|"リダイレクトURL"| BacklogOAuth
    
    BacklogOAuth -->|"認証コード"| AuthAPI
    AuthAPI -->|"コード検証"| AuthService
    AuthService -->|"トークン取得"| BacklogAPI
    AuthService -->|"JWT生成"| JWTHandler
    JWTHandler -->|"Cookie設定"| Browser
    
    Browser -->|"リクエスト"| AuthMiddleware
    AuthMiddleware -->|"JWT検証"| JWTHandler
    AuthMiddleware -->|"権限チェック"| RBACChecker
    RBACChecker -->|"ロール確認"| DB
    
    style Browser fill:#f9f
    style BacklogOAuth fill:#bbf
    style DB fill:#f96
```

### なぜこの構成なのか？

- **Backlog OAuth**: 
  - ユーザーは既存のBacklogアカウントでログイン
  - 新たなパスワードを覚える必要がない
  - セキュアな認証フロー

- **JWT（JSON Web Token）**: 
  - サーバーにセッション情報を保存しない（スケーラブル）
  - トークンに必要な情報を含められる
  - 署名により改ざんを検出可能

- **HttpOnly Cookie**: 
  - JavaScriptからアクセスできない（XSS攻撃を防ぐ）
  - 自動的にリクエストに含まれる（便利）

- **RBAC（Role-Based Access Control）**: 
  - ロール（役割）ベースの柔軟な権限管理
  - 権限の追加・変更が容易

## 🌐 Backlog OAuth 2.0認証フロー

### 📚 OAuth 2.0の重要な用語

実装に入る前に、重要な用語を理解しましょう：

| 用語 | 説明 | 実世界の例 |
|------|------|------------|
| **Client（クライアント）** | 認可を受けるアプリケーション | Team Insight |
| **Resource Owner（リソース所有者）** | データの所有者 | あなた（Backlogユーザー） |
| **Authorization Server（認可サーバー）** | 認可を行うサーバー | Backlogの認証システム |
| **Resource Server（リソースサーバー）** | 保護されたデータを持つサーバー | Backlog API |
| **Authorization Code（認可コード）** | 一時的な引換券 | コンサートチケットの引換券 |
| **Access Token（アクセストークン）** | APIにアクセスするための鍵 | 期間限定の入館証 |
| **Refresh Token（リフレッシュトークン）** | 新しいアクセストークンを取得するための鍵 | 入館証の更新カード |
| **Scope（スコープ）** | アクセスできる範囲の指定 | 入館証で入れるフロアの指定 |
| **State** | CSRF攻撃を防ぐための値 | 申請時の受付番号 |

### 1. 認証フローの全体像

#### 🎭 視覚的に理解する

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant TI as Team Insight<br/>(Frontend)
    participant API as Team Insight<br/>(Backend)
    participant BL as Backlog<br/>(認証)
    participant BAPI as Backlog<br/>(API)

    User->>TI: 1. ログインボタンをクリック
    TI->>API: 2. 認証開始リクエスト
    API->>API: 3. State生成（CSRF対策）
    API->>BL: 4. Backlog認証ページへリダイレクト
    BL->>User: 5. ログイン画面表示
    User->>BL: 6. ID/パスワード入力
    BL->>User: 7. 「Team Insightを許可しますか？」
    User->>BL: 8. 「許可」をクリック
    BL->>API: 9. 認可コード＋State返却
    API->>API: 10. State検証
    API->>BL: 11. 認可コード→トークン交換
    BL->>API: 12. アクセストークン発行
    API->>BAPI: 13. ユーザー情報取得
    BAPI->>API: 14. ユーザーデータ返却
    API->>API: 15. JWT生成＆Cookie設定
    API->>TI: 16. ダッシュボードへリダイレクト
```

#### 📝 各ステップの詳細説明

```
1. ユーザーがログインボタンをクリック
   → ブラウザでTeam Insightのログイン画面を開く

2. Frontend → Backend: GET /api/v1/auth/backlog/authorize
   → 認証プロセスを開始するリクエスト

3. Backend: CSRF対策のState生成
   → ランダムな文字列を生成し、DBに保存（5分間有効）
   → なりすましリクエストを防ぐため

4. Backend → ユーザー: Backlog認証ページへリダイレクト
   → https://[space].backlog.com/OAuth2AccessRequest.action?...

5. ユーザー → Backlog: ログイン & 認可
   → BacklogのID/パスワードを入力
   → 「Team Insightがあなたの情報にアクセスすることを許可しますか？」

6. Backlog → Backend: /api/v1/auth/backlog/callback?code=xxx&state=xxx
   → 認可コード（一時的な引換券）とStateを返却

7. Backend: State検証
   → DBに保存したStateと一致するか確認（CSRF攻撃防止）

8. Backend → Backlog API: アクセストークン取得
   → 認可コードをアクセストークンに交換

9. Backend → Backlog API: ユーザー情報取得
   → 取得したアクセストークンを使ってユーザー情報を取得

10. Backend: ユーザー作成/更新、JWT生成
    → Team InsightのDBにユーザー情報を保存
    → セッション管理用のJWTトークンを生成

11. Backend → Frontend: Cookie設定してリダイレクト
    → HttpOnly CookieにJWTを設定
    → ダッシュボードページへリダイレクト
```

### 2. 実装詳細：認証開始

#### 🔍 必要なインポートと設定

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app import models, deps
from datetime import datetime, timedelta
import secrets  # 安全なランダム文字列生成用
import urllib.parse  # URLパラメータのエンコード用

# APIルーターを作成（エンドポイントをグループ化）
router = APIRouter()
```

#### 🚀 認証開始エンドポイント（実際の実装）

```python
@router.get("/backlog/authorize", response_model=AuthorizationResponse)
async def get_authorization_url(
    space_key: Optional[str] = Query(None, description="Backlogのスペースキー"),
    force_account_selection: bool = Query(False, description="アカウント選択を強制"),
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Backlog OAuth認証を開始するエンドポイント
    
    処理の流れ：
    1. CSRF対策用のstateを生成（space_keyを含む）
    2. stateをデータベースに保存
    3. Backlog認証URLを構築
    4. ユーザーをBacklogへリダイレクト
    """
    import json
    import base64
    
    try:
        # space_keyが指定されていない場合は環境変数のデフォルト値を使用
        if not space_key:
            space_key = settings.BACKLOG_SPACE_KEY
            
        # === STEP 1: 安全なstate生成（拡張版）===
        state_token = secrets.token_urlsafe(32)
        
        # space_keyを含むstateデータを作成
        # これにより、コールバック時にどのスペースからの認証か判別可能
        state_data = {
            "token": state_token,
            "space_key": space_key
        }
        
        # stateデータをBase64エンコード（URLセーフ）
        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
        
        # === STEP 2: stateをデータベースに保存（10分間有効）===
        from zoneinfo import ZoneInfo
        expires_at = datetime.now(ZoneInfo("Asia/Tokyo")) + timedelta(minutes=10)
        
        oauth_state = OAuthState(
            state=state,
            user_id=current_user.id if current_user else None,  # 既存ユーザーの場合
            expires_at=expires_at,
        )
        db.add(oauth_state)
        db.commit()
        
        # === STEP 3: Backlog認証URLを生成 ===
        auth_url, _ = backlog_oauth_service.get_authorization_url(
            space_key=space_key, 
            state=state,
            force_account_selection=force_account_selection
        )
        
        # === STEP 4: レスポンスを返す ===
        response = AuthorizationResponse(
            authorization_url=auth_url, 
            state=state
        )
        # クライアントでの検証用に期待されるスペース情報も返す
        response.expected_space = space_key
        return response
        
    except Exception as e:
        logger.error(f"認証URL生成エラー: {str(e)}", exc_info=True)
        raise ExternalAPIException(
            service="Backlog OAuth",
            detail="認証URLの生成に失敗しました"
        )
```

#### 🔑 実際のBacklog OAuthサービス実装

```python
# backend/app/services/backlog_oauth.py
class BacklogOAuthService:
    """
    Backlog OAuth認証を管理するサービス
    """
    
    def get_authorization_url(
        self, 
        space_key: str, 
        state: str,
        force_account_selection: bool = False
    ) -> Tuple[str, str]:
        """
        Backlog認証URLを生成
        
        Args:
            space_key: Backlogスペースキー
            state: CSRF対策用のstate
            force_account_selection: アカウント選択を強制するか
            
        Returns:
            (authorization_url, state)のタプル
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        
        # アカウント選択を強制する場合
        if force_account_selection:
            params["select_account"] = "true"
        
        query_string = urllib.parse.urlencode(params)
        auth_url = f"{self.auth_base_url.format(space_key=space_key)}?{query_string}"
        
        return auth_url, state
```

#### 💡 ポイント解説

1. **`@router.get("/backlog/authorize")`**
   - HTTPのGETメソッドで `/api/v1/auth/backlog/authorize` にアクセスされた時に実行
   - ユーザーがログインボタンをクリックした時に呼ばれる

2. **`db: Session = Depends(deps.get_db)`**
   - FastAPIの依存性注入（DI）
   - データベースセッションを自動的に取得・管理
   - リクエスト終了時に自動的にクローズ

3. **CSRF（Cross-Site Request Forgery）攻撃とは？**
   ```
   悪意のあるサイト：「Team Insightの認証を勝手に実行」
   ↓
   ユーザーのブラウザ → Team Insight（ユーザーの意図しない操作）
   
   対策：stateパラメータで正当なリクエストか確認
   ```

### 3. 実装詳細：コールバック処理

#### 🎯 コールバックエンドポイント（実際の実装）

```python
@router.post("/backlog/callback", response_model=TokenResponse)
async def handle_callback(
    request: CallbackRequest,  # codeとstateを含むリクエスト
    http_request: Request,    # HTTPリクエスト情報（IP、User-Agent等）
    db: Session = Depends(get_db_session),
    auth_service: BacklogAuthService = Depends(get_auth_service)
):
    """
    Backlog OAuth認証のコールバック処理
    
    Backlogでの認証成功後、このエンドポイントが呼ばれる
    処理の流れ：
    1. stateの検証（CSRF対策）
    2. 認証コードをアクセストークンに交換
    3. ユーザー情報を取得
    4. ユーザーの作成/更新
    5. JWTトークン生成とCookie設定
    """
    logger.info(
        f"認証コールバック開始 - code: {request.code[:10]}..., state: {request.state}"
    )
    
    # ========================================
    # STEP 1: State検証（CSRF対策）
    # ========================================
    
    # サービスクラスを使ってstateを検証
    oauth_state = auth_service.validate_oauth_state(db, request.state)
    
    try:
        # stateからspace_keyを取り出す
        space_key = auth_service.extract_space_key_from_state(request.state)
    
    # ========================================
    # STEP 2: 認可コード → アクセストークン交換
    # ========================================
    
    # トークン取得用のパラメータ
    token_data = {
        "grant_type": "authorization_code",  # 認可コードフロー
        "code": code,  # Backlogから受け取った認可コード
        "redirect_uri": settings.BACKLOG_REDIRECT_URI,  # 登録時と同じURI
        "client_id": settings.BACKLOG_CLIENT_ID,  # アプリID
        "client_secret": settings.BACKLOG_CLIENT_SECRET,  # アプリシークレット
    }
    
    # BacklogのトークンエンドポイントにPOST
    import httpx  # HTTPクライアントライブラリ
    
    token_response = httpx.post(
        f"https://{settings.BACKLOG_SPACE_KEY}.backlog.com/api/v2/oauth2/token",
        data=token_data  # application/x-www-form-urlencoded形式
    )
    
    if token_response.status_code != 200:
        # トークン取得失敗
        logger.error(f"Token exchange failed: {token_response.text}")
        raise HTTPException(
            status_code=400, 
            detail="アクセストークンの取得に失敗しました"
        )
    
    # レスポンスの例：
    # {
    #   "access_token": "eyJhbGc...",
    #   "token_type": "Bearer",
    #   "expires_in": 3600,
    #   "refresh_token": "def502..."
    # }
    tokens = token_response.json()
    
    # ========================================
    # STEP 3: ユーザー情報取得
    # ========================================
    
    # 取得したアクセストークンでBacklog APIを呼び出し
    user_response = httpx.get(
        "https://api.backlog.com/api/v2/users/myself",  # 自分の情報
        headers={
            "Authorization": f"Bearer {tokens['access_token']}"  # Bearer認証
        }
    )
    
    if user_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="ユーザー情報の取得に失敗しました"
        )
    
    # レスポンスの例：
    # {
    #   "id": 12345,
    #   "userId": "tanaka",
    #   "name": "田中太郎",
    #   "mailAddress": "tanaka@example.com",
    #   ...
    # }
    user_data = user_response.json()
    
    # ========================================
    # STEP 4: ユーザー作成/更新
    # ========================================
    
    # Backlog IDでユーザーを検索
    user = db.query(User).filter(
        User.backlog_id == user_data["id"]
    ).first()
    
    if not user:
        # 新規ユーザー作成
        user = User(
            backlog_id=user_data["id"],  # Backlogのユーザーid
            email=user_data["mailAddress"],
            name=user_data["name"],
            is_active=True  # デフォルトでアクティブ
        )
        db.add(user)
        logger.info(f"新規ユーザー作成: {user.email}")
    else:
        # 既存ユーザー更新
        user.name = user_data["name"]  # 名前が変わっているかも
        user.email = user_data["mailAddress"]  # メールが変わっているかも
        user.last_login = datetime.utcnow()  # 最終ログイン時刻
        logger.info(f"既存ユーザー更新: {user.email}")
    
    # ========================================
    # STEP 5: Backlog OAuthトークン保存
    # ========================================
    
    # Backlog APIを使うためのトークンを保存
    oauth_token = OAuthToken(
        user_id=user.id,
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),  # オプショナル
        expires_at=datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
    )
    db.add(oauth_token)
    db.commit()  # ここまでの変更をDBに保存
    
    # ========================================
    # STEP 6: Team Insight用のJWT生成
    # ========================================
    
    # セッション管理用のJWTトークンを生成
    access_token = create_access_token(
        data={
            "sub": str(user.id),  # subject = ユーザーID
            "email": user.email,  # 追加情報
            "name": user.name
        },
        expires_delta=timedelta(minutes=30)  # 30分有効
    )
    
    # ========================================
    # STEP 7: HttpOnly Cookieに設定
    # ========================================
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,     # JavaScriptからアクセス不可（XSS対策）
        secure=True,       # HTTPS必須（本番環境）
        samesite="lax",    # CSRF対策（strictだと厳しすぎる）
        max_age=1800,      # 30分（秒単位）
        path="/"           # 全てのパスで有効
    )
    
    # 開発環境の場合はsecure=Falseにする必要あり
    # if settings.ENVIRONMENT == "development":
    #     secure = False
    
    # ========================================
    # STEP 8: フロントエンドへリダイレクト
    # ========================================
    
    # 認証成功！ダッシュボードへ
    redirect_url = f"{settings.FRONTEND_URL}/dashboard"
    
    # エラーの場合は別のページへ
    # redirect_url = f"{settings.FRONTEND_URL}/auth/error?reason=..."
    
    return RedirectResponse(url=redirect_url)
```

#### 🔒 セキュリティポイント

1. **State検証を必ず最初に行う**
   - 不正なリクエストを早期に検出
   - 使用済みStateは即削除

2. **トークンは暗号化して保存**
   - 本番環境では暗号化必須
   - アクセストークンは機密情報

3. **エラー詳細を隠す**
   - 攻撃者にヒントを与えない
   - ユーザーには一般的なメッセージ

### AuthServiceクラスの詳細実装

```python
# backend/app/services/auth_service.py
class AuthService:
    """認証関連のビジネスロジックを管理するサービス"""
    
    def validate_oauth_state(self, db: Session, state: str) -> OAuthState:
        """
        OAuthのstateパラメータを検証
        
        Args:
            db: データベースセッション
            state: 検証するstateパラメータ
            
        Returns:
            有効なOAuthStateオブジェクト
            
        Raises:
            ValidationException: stateが無効または期限切れの場合
        """
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()
        
        if not oauth_state:
            logger.error(f"無効なstateパラメータ - state: {state}")
            raise ValidationException(detail="無効なstateパラメータです")
        
        if oauth_state.is_expired():
            logger.error(f"stateパラメータの有効期限切れ - state: {state}")
            db.delete(oauth_state)
            db.commit()
            raise ValidationException(detail="stateパラメータの有効期限が切れています")
        
        return oauth_state
    
    def find_or_create_user(self, db: Session, user_info: dict) -> User:
        """
        Backlogユーザー情報からTeam Insightユーザーを作成/更新
        
        Args:
            db: データベースセッション
            user_info: Backlogから取得したユーザー情報
            
        Returns:
            作成/更新されたユーザーオブジェクト
        """
        user = db.query(User).filter(
            User.backlog_id == user_info["id"]
        ).first()
        
        if not user:
            # 新規ユーザー作成
            user = User(
                backlog_id=user_info["id"],
                email=user_info["mailAddress"],
                name=user_info["name"],
                user_id=user_info.get("userId"),  # BacklogユーザーID
                is_active=True,
                role_id=user_info.get("roleType", 2),  # デフォルト: 一般ユーザー
            )
            db.add(user)
            logger.info(f"新規ユーザー作成: {user.email}")
        else:
            # 既存ユーザー更新
            user.email = user_info["mailAddress"]
            user.name = user_info["name"]
            user.user_id = user_info.get("userId")
            logger.info(f"既存ユーザー更新: {user.email}")
        
        return user
    
    def assign_default_role_if_needed(self, db: Session, user: User) -> User:
        """
        ユーザーにデフォルトロールを割り当て
        
        Args:
            db: データベースセッション
            user: ユーザーオブジェクト
            
        Returns:
            ロールが割り当てられたユーザー
        """
        if not user.user_roles:
            # デフォルトロール（MEMBER）を付与
            member_role = db.query(Role).filter(Role.name == "MEMBER").first()
            if member_role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=member_role.id
                )
                db.add(user_role)
                db.commit()
                
                # リレーションをリロード
                db.refresh(user)
                logger.info(f"デフォルトロールを割り当て: {user.email} -> MEMBER")
        
        return user
```

## 🎫 JWTトークン管理

### 📘 JWT（JSON Web Token）とは？

#### 🎟️ 日常生活で例えると

JWTは「デジタル身分証明書」のようなものです：

```
現実世界の身分証明書：
┌─────────────────────────┐
│ 氏名: 田中太郎          │
│ 生年月日: 1990/01/01    │
│ 有効期限: 2025/12/31    │
│ 発行者: 警察署          │
│ [署名・印鑑]           │
└─────────────────────────┘

JWT：
┌─────────────────────────┐
│ Header: 暗号化方式      │
│ Payload: ユーザー情報   │
│ Signature: デジタル署名 │
└─────────────────────────┘
```

#### 🔧 JWTの構造

JWTは3つの部分から構成され、ピリオド（.）で区切られています：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
└─────────Header──────────┘.└───────────────Payload────────────────┘.└─────────Signature──────────┘
```

**1. Header（ヘッダー）**
```json
{
  "alg": "HS256",  // 署名アルゴリズム
  "typ": "JWT"     // トークンタイプ
}
```

**2. Payload（ペイロード）**
```json
{
  "sub": "1234567890",      // Subject: ユーザーID
  "name": "田中太郎",       // カスタムクレーム
  "email": "tanaka@example.com",
  "iat": 1516239022,        // Issued At: 発行時刻
  "exp": 1516242622         // Expiration: 有効期限
}
```

**3. Signature（署名）**
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

#### 🤔 なぜJWTを使うのか？

**従来のセッション管理**：
```
1. ログイン → サーバーがセッションID発行
2. サーバー側でセッション情報を保存（メモリ/DB）
3. 毎回のリクエストでセッションIDを確認

問題点：
- サーバーのメモリ/DBに負荷
- スケールアウトが困難
- サーバー間でセッション共有が必要
```

**JWT方式**：
```
1. ログイン → サーバーがJWT発行
2. クライアント側でJWTを保存（Cookie）
3. 毎回のリクエストでJWTの署名を検証

利点：
- サーバーに状態を持たない（ステートレス）
- スケールアウトが容易
- マイクロサービスに適している
```

### JWT生成と検証

#### 🔐 JWT生成の実装

```python
# backend/app/core/security.py
from jose import jwt, JWTError  # python-jose ライブラリ
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.core.config import settings

# 署名アルゴリズム
# HS256 = HMAC + SHA256（対称鍵暗号）
# RS256 = RSA + SHA256（公開鍵暗号）も選択可能
ALGORITHM = "HS256"

def create_access_token(
    data: Dict[str, Any],  # JWTに含めるデータ
    expires_delta: Optional[timedelta] = None  # 有効期限
) -> str:
    """
    アクセストークンを生成
    
    Args:
        data: ペイロードに含めるデータ
              例: {"sub": "user_id", "email": "user@example.com"}
        expires_delta: トークンの有効期限
                      例: timedelta(minutes=30)
    
    Returns:
        str: エンコードされたJWT文字列
    """
    # データをコピー（元のデータを変更しないため）
    to_encode = data.copy()
    
    # === 有効期限の設定 ===
    if expires_delta:
        # 指定された期限を使用
        expire = datetime.utcnow() + expires_delta
    else:
        # デフォルト: 30分
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    # === 標準クレームの追加 ===
    to_encode.update({
        "exp": expire,              # Expiration Time: 有効期限
        "iat": datetime.utcnow(),   # Issued At: 発行時刻
        "type": "access",           # カスタムクレーム: トークンタイプ
        # "iss": "team-insight",    # Issuer: 発行者（オプション）
        # "aud": "team-insight-api" # Audience: 想定利用者（オプション）
    })
    
    # === JWTのエンコード ===
    # 1. ヘッダーとペイロードをBase64エンコード
    # 2. SECRET_KEYで署名を作成
    # 3. 3つの部分を.で結合
    encoded_jwt = jwt.encode(
        to_encode,              # ペイロード
        settings.SECRET_KEY,    # 署名用の秘密鍵（絶対に漏らさない！）
        algorithm=ALGORITHM     # 署名アルゴリズム
    )
    
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    トークンを検証してペイロードを返す
    
    Args:
        token: 検証するJWT文字列
    
    Returns:
        Dict: 検証成功時はペイロード、失敗時はNone
    """
    try:
        # === JWTのデコードと検証 ===
        # 1. 署名を検証（SECRET_KEYで署名が正しいか確認）
        # 2. 有効期限を確認（exp クレーム）
        # 3. ペイロードを返す
        payload = jwt.decode(
            token,                      # JWT文字列
            settings.SECRET_KEY,        # 検証用の秘密鍵
            algorithms=[ALGORITHM]      # 許可するアルゴリズム（複数可）
        )
        
        # 追加の検証（必要に応じて）
        # if payload.get("type") != "access":
        #     return None
        
        return payload
        
    except JWTError as e:
        # JWTError の種類：
        # - ExpiredSignatureError: トークンの有効期限切れ
        # - InvalidTokenError: 不正なトークン形式
        # - InvalidSignatureError: 署名が一致しない
        logger.error(f"JWT検証エラー: {str(e)}")
        return None

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    リフレッシュトークンを生成（長期間有効）
    
    リフレッシュトークンの用途：
    - アクセストークンが期限切れになった時の再発行用
    - より長い有効期限（例: 7日間）
    - 別のタイプとして識別
    """
    to_encode = data.copy()
    
    # リフレッシュトークンは長期間有効
    expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"  # タイプを明示
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
```

#### 🔍 JWTのセキュリティ考慮点

```python
# セキュリティのベストプラクティス

1. SECRET_KEYの管理
   - 環境変数で管理（コードに直接書かない）
   - 十分な長さ（256ビット以上推奨）
   - 定期的な更新

2. トークンの有効期限
   - アクセストークン: 短め（15-30分）
   - リフレッシュトークン: 長め（7-30日）
   - 用途に応じて調整

3. ペイロードの内容
   - 機密情報を含めない（パスワード等）
   - 必要最小限の情報のみ
   - Base64エンコードは暗号化ではない！

4. HTTPS必須
   - トークンは平文で送信される
   - 中間者攻撃を防ぐためHTTPS必須
```

### Cookie からのトークン取得

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, Cookie
from typing import Optional

async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    """現在のユーザーを取得"""
    
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="認証が必要です"
        )
    
    # トークン検証
    payload = verify_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="無効なトークンです"
        )
    
    # ユーザー取得
    user_id = payload.get("sub")
    user = db.query(User).filter(
        User.id == user_id,
        User.is_active == True  # アクティブユーザーのみ
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="ユーザーが見つかりません"
        )
    
    return user
```

### リフレッシュトークンの実装

```python
@router.post("/refresh")
async def refresh_token(
    refresh_token: str = Cookie(None),
    response: Response = Response(),
    db: Session = Depends(deps.get_db)
):
    """トークンをリフレッシュ"""
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="リフレッシュトークンがありません")
    
    # リフレッシュトークン検証
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="無効なリフレッシュトークン")
    
    # 新しいアクセストークン生成
    user_id = payload.get("sub")
    new_access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(minutes=30)
    )
    
    # Cookie更新
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1800
    )
    
    return {"message": "トークンを更新しました"}
```

## 🛡️ RBAC（ロールベースアクセス制御）

### 📚 RBACとは？

#### 🏢 会社組織で例えると

RBACは「役職による権限管理」のようなものです：

```
会社組織の例：
┌─────────────┐
│    社長     │ → 全ての権限
├─────────────┤
│   部長      │ → 部署内の承認権限
├─────────────┤
│  チーム     │ → プロジェクト管理権限
│  リーダー   │
├─────────────┤
│   社員      │ → 基本的な作業権限
└─────────────┘

Team InsightのRBAC：
┌─────────────┐
│   ADMIN     │ → システム全体の管理権限
├─────────────┤
│  PROJECT_   │ → プロジェクト管理権限
│  LEADER     │
├─────────────┤
│   MEMBER    │ → 基本的な閲覧・操作権限
└─────────────┘
```

#### 🔑 RBACの基本概念

**1. ユーザー（User）**
```
田中さん、佐藤さん、鈴木さん...
```

**2. ロール（Role）**
```
管理者、プロジェクトリーダー、メンバー
```

**3. 権限（Permission）**
```
ユーザー作成、プロジェクト編集、レポート閲覧...
```

**4. 関係性**
```
ユーザー → ロール → 権限

例：
田中さん → 管理者 → [ユーザー作成、プロジェクト編集、レポート閲覧]
佐藤さん → メンバー → [レポート閲覧]
```

#### 🎯 なぜRBACが必要か？

**権限を直接管理する場合の問題**：
```
ユーザー100人 × 権限50個 = 5,000個の設定が必要！

田中さん: [権限A, 権限B, 権限C, ...]
佐藤さん: [権限A, 権限B, 権限C, ...]
鈴木さん: [権限A, 権限B, 権限C, ...]
（全員分設定が必要...）
```

**RBACを使った場合**：
```
ロール3個 × 権限50個 = 150個の設定で済む！

管理者ロール: [権限A, 権限B, 権限C, ...]
田中さん → 管理者ロール
佐藤さん → 管理者ロール
（ロールを割り当てるだけ！）
```

### データベース設計

#### 📊 RBACのテーブル構造

```sql
-- ========================================
-- 1. ロールテーブル（役職を定義）
-- ========================================
CREATE TABLE team_insight.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- 一意のID
    name VARCHAR(50) UNIQUE NOT NULL,                -- ロール名（ADMIN, PROJECT_LEADER, MEMBER）
    description TEXT,                                -- 説明（例：「システム管理者」）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- 作成日時
);

-- サンプルデータ
INSERT INTO team_insight.roles (name, description) VALUES 
('ADMIN', 'システム全体の管理権限を持つ'),
('PROJECT_LEADER', 'プロジェクトの管理権限を持つ'),
('MEMBER', '基本的な操作権限を持つ');

-- ========================================
-- 2. 権限テーブル（できることを定義）
-- ========================================
CREATE TABLE team_insight.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource VARCHAR(50) NOT NULL,  -- リソース名（操作対象）
    action VARCHAR(50) NOT NULL,    -- アクション（操作内容）
    UNIQUE(resource, action)        -- 同じ権限は1つだけ
);

-- サンプルデータ
INSERT INTO team_insight.permissions (resource, action) VALUES 
('users', 'read'),      -- ユーザー情報を閲覧
('users', 'write'),     -- ユーザー情報を編集
('users', 'delete'),    -- ユーザーを削除
('projects', 'read'),   -- プロジェクトを閲覧
('projects', 'write'),  -- プロジェクトを編集
('projects', 'delete'), -- プロジェクトを削除
('reports', 'read'),    -- レポートを閲覧
('reports', 'write');   -- レポートを作成

-- ========================================
-- 3. ユーザーロール関連テーブル（誰がどの役職か）
-- ========================================
CREATE TABLE team_insight.user_roles (
    user_id UUID REFERENCES team_insight.users(id),        -- ユーザーID
    role_id UUID REFERENCES team_insight.roles(id),        -- ロールID
    project_id UUID REFERENCES team_insight.projects(id),  -- プロジェクトID（NULL=全体）
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,        -- 割り当て日時
    assigned_by UUID REFERENCES team_insight.users(id),    -- 割り当て者
    PRIMARY KEY (user_id, role_id, project_id)
);

-- project_idの意味：
-- NULL: グローバルロール（システム全体）
-- UUID: プロジェクト固有のロール

-- ========================================
-- 4. ロール権限関連テーブル（役職は何ができるか）
-- ========================================
CREATE TABLE team_insight.role_permissions (
    role_id UUID REFERENCES team_insight.roles(id),
    permission_id UUID REFERENCES team_insight.permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- デフォルトの権限設定例
-- ADMINロール: 全権限
INSERT INTO team_insight.role_permissions 
SELECT r.id, p.id 
FROM team_insight.roles r, team_insight.permissions p 
WHERE r.name = 'ADMIN';

-- MEMBERロール: 読み取りのみ
INSERT INTO team_insight.role_permissions 
SELECT r.id, p.id 
FROM team_insight.roles r, team_insight.permissions p 
WHERE r.name = 'MEMBER' AND p.action = 'read';
```

#### 🔗 テーブル間の関係

```mermaid
graph LR
    User[ユーザー] -->|N:M| UserRole[ユーザーロール]
    UserRole -->|M:1| Role[ロール]
    Role -->|N:M| RolePermission[ロール権限]
    RolePermission -->|M:1| Permission[権限]
    UserRole -->|M:1| Project[プロジェクト]
    
    style User fill:#f9f,stroke:#333,stroke-width:2px
    style Role fill:#bbf,stroke:#333,stroke-width:2px
    style Permission fill:#bfb,stroke:#333,stroke-width:2px
```

#### 💡 設計のポイント

1. **グローバルロール vs プロジェクトロール**
   ```sql
   -- グローバル管理者（全プロジェクトに権限）
   INSERT INTO user_roles (user_id, role_id, project_id) 
   VALUES ('user-123', 'admin-role-id', NULL);
   
   -- プロジェクト限定リーダー
   INSERT INTO user_roles (user_id, role_id, project_id) 
   VALUES ('user-456', 'leader-role-id', 'project-789');
   ```

2. **権限の組み合わせ**
   ```
   resource.action の形式で権限を表現
   例: "users.write" = ユーザー情報の編集権限
   ```

3. **拡張性**
   - 新しいロールの追加が簡単
   - 新しい権限の追加も簡単
   - 既存ユーザーへの影響なし

### 権限チェックの実装

#### 🔐 権限チェッカークラス

```python
# backend/app/core/permissions.py
from typing import List, Optional, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, deps

class PermissionChecker:
    """
    権限チェックを行うクラス
    FastAPIの依存性注入システムと連携して動作
    """
    
    def __init__(self, required_permissions: List[str]):
        """
        Args:
            required_permissions: 必要な権限のリスト
                                 例: ["users.read", "projects.write"]
        """
        self.required_permissions = required_permissions
    
    def __call__(
        self,
        current_user: models.User = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db)
    ) -> bool:
        """
        権限チェックの実行
        FastAPIから自動的に呼ばれる（依存性注入）
        
        Args:
            current_user: 現在のログインユーザー
            db: データベースセッション
            
        Returns:
            bool: 権限がある場合True
            
        Raises:
            HTTPException: 権限がない場合403エラー
        """
        # === STEP 1: ユーザーの全権限を取得 ===
        user_permissions = self._get_user_permissions(current_user, db)
        
        # デバッグ用ログ
        logger.debug(f"ユーザー {current_user.email} の権限: {user_permissions}")
        logger.debug(f"必要な権限: {self.required_permissions}")
        
        # === STEP 2: 必要な権限がすべてあるかチェック ===
        missing_permissions = []
        
        for permission in self.required_permissions:
            if permission not in user_permissions:
                missing_permissions.append(permission)
        
        # === STEP 3: 権限が不足している場合はエラー ===
        if missing_permissions:
            logger.warning(
                f"権限不足: ユーザー {current_user.email} に "
                f"{missing_permissions} の権限がありません"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "権限が不足しています",
                    "required": self.required_permissions,
                    "missing": missing_permissions
                }
            )
        
        return True
    
    def _get_user_permissions(
        self, 
        user: models.User, 
        db: Session
    ) -> Set[str]:
        """
        ユーザーの全権限を取得
        
        処理の流れ：
        1. ユーザーが持つロールを取得
        2. 各ロールが持つ権限を取得
        3. "resource.action" 形式で返す
        """
        # === 複雑なJOINクエリの説明 ===
        # permissions テーブル
        #     ↓ JOIN
        # role_permissions テーブル（中間テーブル）
        #     ↓ JOIN
        # roles テーブル
        #     ↓ JOIN
        # user_roles テーブル（中間テーブル）
        #     ↓ WHERE
        # 特定のユーザー
        
        permissions = db.query(models.Permission).join(
            models.role_permissions,  # 中間テーブル
            models.Permission.id == models.role_permissions.c.permission_id
        ).join(
            models.Role,
            models.Role.id == models.role_permissions.c.role_id
        ).join(
            models.user_roles,  # 中間テーブル
            models.Role.id == models.user_roles.c.role_id
        ).filter(
            models.user_roles.c.user_id == user.id
        ).all()
        
        # Set型で重複を自動除去
        return {f"{p.resource}.{p.action}" for p in permissions}

# ========================================
# 便利なデコレータ版
# ========================================

def require_permissions(*permissions: str):
    """
    権限チェックデコレータ
    
    使用例：
    @router.get("/admin/users")
    @require_permissions("users.read", "users.write")
    async def get_users():
        ...
    """
    def decorator(func):
        # FastAPIの依存性として権限チェッカーを追加
        func.__dependencies__ = getattr(func, '__dependencies__', [])
        func.__dependencies__.append(
            Depends(PermissionChecker(list(permissions)))
        )
        return func
    return decorator

# ========================================
# ロール別の便利な関数
# ========================================

def require_admin():
    """管理者権限を要求"""
    async def check_admin(
        current_user: models.User = Depends(deps.get_current_user),
        db: Session = Depends(deps.get_db)
    ):
        user_roles = db.query(models.Role).join(
            models.user_roles,
            models.Role.id == models.user_roles.c.role_id
        ).filter(
            models.user_roles.c.user_id == current_user.id,
            models.Role.name == "ADMIN"
        ).first()
        
        if not user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理者権限が必要です"
            )
        
        return True
    
    return Depends(check_admin)
```

### エンドポイントでの使用例

```python
@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(PermissionChecker(["users.write"]))]
)
async def assign_role_to_user(
    user_id: UUID,
    role_name: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """ユーザーにロールを割り当て（users.write権限が必要）"""
    
    # ADMINロールは特別な権限が必要
    if role_name == "ADMIN":
        admin_checker = PermissionChecker(["system.admin"])
        admin_checker(current_user, db)
    
    # ロールを割り当て
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="ロールが見つかりません")
    
    user_role = UserRole(user_id=user_id, role_id=role.id)
    db.add(user_role)
    db.commit()
    
    return {"message": f"ロール {role_name} を割り当てました"}
```

## 🎭 フロントエンドでの認証処理

### 認証状態の管理

```tsx
// frontend/src/hooks/useAuth.ts
import { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useRouter } from 'next/navigation'
import { authService } from '@/services/authService'
import { setUser, logout } from '@/store/slices/authSlice'
import { RootState } from '@/store'

export const useAuth = () => {
  const dispatch = useDispatch()
  const router = useRouter()
  const { user, isAuthenticated, loading } = useSelector(
    (state: RootState) => state.auth
  )

  // 初回マウント時に認証状態を確認
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await authService.verify()
        dispatch(setUser(response.user))
      } catch (error) {
        dispatch(setUser(null))
      }
    }
    
    checkAuth()
  }, [dispatch])

  const handleLogout = async () => {
    try {
      await authService.logout()
      dispatch(logout())
      router.push('/auth/login')
    } catch (error) {
      console.error('ログアウトエラー:', error)
    }
  }

  return {
    user,
    isAuthenticated,
    loading,
    logout: handleLogout,
  }
}
```

### 保護されたルート

```tsx
// frontend/src/components/auth/ProtectedRoute.tsx
'use client'

import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'

interface Props {
  children: React.ReactNode
  requiredRoles?: string[]
}

export function ProtectedRoute({ children, requiredRoles }: Props) {
  const { user, isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [loading, isAuthenticated, router])

  // ロールチェック
  useEffect(() => {
    if (user && requiredRoles && requiredRoles.length > 0) {
      const userRoles = user.user_roles.map(ur => ur.role.name)
      const hasRequiredRole = requiredRoles.some(role => 
        userRoles.includes(role)
      )
      
      if (!hasRequiredRole) {
        router.push('/403') // 権限なしページ
      }
    }
  }, [user, requiredRoles, router])

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
```

### APIクライアントの認証対応

```tsx
// frontend/src/lib/api-client.ts
import axios from 'axios'
import { toast } from '@/components/ui/use-toast'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Cookie を送信
  headers: {
    'Content-Type': 'application/json',
  },
})

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 401エラーでリフレッシュ未試行の場合
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // トークンリフレッシュ
        await apiClient.post('/api/v1/auth/refresh')
        
        // 元のリクエストを再実行
        return apiClient(originalRequest)
      } catch (refreshError) {
        // リフレッシュ失敗 → ログイン画面へ
        window.location.href = '/auth/login'
        return Promise.reject(refreshError)
      }
    }

    // その他のエラー
    if (error.response?.status === 403) {
      toast({
        title: 'アクセス拒否',
        description: 'この操作を実行する権限がありません',
        variant: 'destructive',
      })
    }

    return Promise.reject(error)
  }
)

export default apiClient
```

## 🔒 セキュリティのベストプラクティス

### 1. トークンの保護

```python
# backend: HttpOnly Cookie の設定
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,      # JavaScriptからアクセス不可
    secure=True,        # HTTPS必須
    samesite="strict",  # CSRF攻撃を防ぐ
    max_age=1800,       # 30分で期限切れ
    path="/"            # パス制限
)
```

### 2. CSRF対策

```python
# Double Submit Cookie パターン
@router.post("/api/v1/sensitive-action")
async def sensitive_action(
    csrf_token: str = Header(None),
    csrf_cookie: str = Cookie(None),
    current_user: User = Depends(deps.get_current_user)
):
    # CSRFトークンの検証
    if not csrf_token or csrf_token != csrf_cookie:
        raise HTTPException(status_code=403, detail="CSRF token invalid")
    
    # 処理を実行
    return {"status": "success"}
```

### 3. レート制限

```python
# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 使用例
@router.post("/auth/login")
@limiter.limit("5 per minute")  # 1分間に5回まで
async def login(request: Request, ...):
    pass
```

### 4. セキュリティヘッダー

```python
# backend/app/core/security_headers.py
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # セキュリティヘッダーを追加
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## 📝 認証フローのデバッグ

### よくある問題と解決方法

1. **「Invalid state」エラー**
   - 原因: CSRF state の有効期限切れ
   - 解決: ログインページに戻って再試行

2. **「space_not_allowed」エラー**
   - 原因: 異なるBacklogスペースのアカウント
   - 解決: 正しいスペースのアカウントでログイン

3. **Cookie が設定されない**
   - 原因: SameSite 設定の問題
   - 解決: 開発環境では `samesite="lax"` を使用

### デバッグ用ログ

```python
# 認証フローのデバッグログ
logger.debug(f"OAuth state created: {state}")
logger.debug(f"Redirect URL: {auth_url}")
logger.info(f"User authenticated: {user.email}")
logger.warning(f"Failed authentication attempt for: {email}")
```

---

次は[データベース設計と操作](06-database.md)で、SQLAlchemyを使ったデータベース操作を学びましょう！