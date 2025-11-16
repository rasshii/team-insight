"""
セキュリティ関連のユーティリティ

このモジュールは、Team InsightアプリケーションのセキュリティとJWT認証機能を提供します。
Backlog OAuthを使用した認証フローを実装しており、パスワードベースの認証は使用しません。

主要な機能:
    1. JWT（JSON Web Token）トークンの生成と検証
       - アクセストークン: 短期間有効（デフォルト15分）
       - リフレッシュトークン: 長期間有効（デフォルト30日）

    2. Cookie/Headerベースの認証
       - Authorizationヘッダーからのトークン取得
       - HTTPOnlyクッキーからのトークン取得（XSS対策）

    3. ユーザー認証状態の管理
       - 現在のユーザー取得（オプショナル）
       - アクティブユーザーの取得（必須）
       - スーパーユーザー権限のチェック

主要なクラス・関数:
    - create_access_token(): アクセストークンを生成
    - create_refresh_token(): リフレッシュトークンを生成
    - decode_token(): JWTトークンをデコード
    - get_current_user(): 現在のユーザーを取得（認証なしでも可）
    - get_current_active_user(): アクティブユーザーを取得（認証必須）
    - get_current_active_superuser(): スーパーユーザーを取得（管理者のみ）

セキュリティの考慮事項:
    - JWT署名にHS256アルゴリズムを使用
    - トークンに有効期限を設定してセッションハイジャック対策
    - HTTPOnlyクッキーでXSS攻撃からトークンを保護
    - リフレッシュトークンとアクセストークンを分離して、セキュリティリスクを最小化

使用例:
    ```python
    from fastapi import Depends
    from app.core.security import get_current_active_user

    @router.get("/profile")
    async def get_profile(current_user: User = Depends(get_current_active_user)):
        # current_userは認証済みのユーザー
        return {"username": current_user.username}

    # トークン生成
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": str(user.id)})
    ```

注意事項:
    - トークンの有効期限は環境変数で設定可能（.envファイルを参照）
    - 本番環境では必ずHTTPSを使用してください（トークン漏洩防止）
    - SECRET_KEYは十分に複雑な値を設定してください
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

# OAuth2スキーム
# FastAPIのOAuth2PasswordBearerを使用してAuthorizationヘッダーからトークンを取得
# auto_error=False: トークンがない場合でもエラーにしない（オプショナル認証に対応）
# tokenUrl: OpenAPI仕様用のトークンエンドポイントURL（ドキュメントに表示される）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

# JWT設定
# HS256 (HMAC with SHA-256): 秘密鍵を使った対称暗号化アルゴリズム
# RS256 (RSA)よりシンプルで、単一サーバー環境では十分なセキュリティを提供
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを生成します

    アクセストークンは短期間有効で、APIリクエストの認証に使用されます。
    有効期限が短いため、トークンが漏洩した場合の被害を最小限に抑えられます。

    処理フロー:
        1. ペイロードデータをコピー（元データを変更しないため）
        2. 有効期限を計算（デフォルトまたはカスタム）
        3. exp（有効期限）とtype（トークンタイプ）をペイロードに追加
        4. SECRET_KEYで署名してJWTトークンを生成

    Args:
        data (dict): トークンに含めるデータ。通常は{"sub": "user_id"}形式。
                    "sub"（subject）はJWT標準クレームでユーザーIDを表します。
        expires_delta (Optional[timedelta], optional): トークンの有効期限。
                    指定しない場合は設定ファイルのACCESS_TOKEN_EXPIRE_MINUTES（通常15分）を使用。
                    カスタム有効期限が必要な場合（例: テスト用に長期間有効なトークン）に指定。

    Returns:
        str: エンコードされたJWTトークン文字列。
             形式: "header.payload.signature" (Base64エンコード)

    Examples:
        >>> # 通常の使用（デフォルトの有効期限）
        >>> token = create_access_token(data={"sub": "123"})

        >>> # カスタムの有効期限
        >>> from datetime import timedelta
        >>> token = create_access_token(
        ...     data={"sub": "123"},
        ...     expires_delta=timedelta(hours=1)
        ... )

    Note:
        - トークンには機密情報を含めないでください（JWTはデコード可能です）
        - 生成されたトークンは署名されていますが、暗号化されていません
        - クライアント側でトークンを安全に保管する必要があります

    セキュリティ:
        - SECRET_KEYは環境変数で管理され、決してコードにハードコードしません
        - 有効期限を短く設定することで、トークン漏洩時のリスクを軽減
    """
    import logging

    logger = logging.getLogger(__name__)

    # ペイロードデータのコピーを作成（元データを変更しないため）
    to_encode = data.copy()

    # 有効期限の計算
    if expires_delta:
        # カスタムの有効期限が指定された場合
        expire = datetime.utcnow() + expires_delta
    else:
        # デフォルトの有効期限を使用（設定ファイルから取得）
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # JWT標準クレームを追加
    # exp: 有効期限（UNIX timestamp）- JWT標準クレーム
    # type: トークンタイプ（カスタムクレーム）- access/refreshを区別
    to_encode.update({"exp": expire, "type": "access"})
    logger.debug(f"Creating token with payload: {to_encode}, expire: {expire}")

    # JWTトークンをエンコード（署名付き）
    # settings.SECRET_KEY: 署名用の秘密鍵（環境変数から取得）
    # ALGORITHM: 署名アルゴリズム（HS256）
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created token: {encoded_jwt[:20]}...")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTリフレッシュトークンを生成します

    リフレッシュトークンは長期間有効で、アクセストークンを再発行するために使用されます。
    アクセストークンの有効期限が切れた際に、リフレッシュトークンを使用して
    新しいアクセストークンを取得することで、ユーザーは再ログインせずにサービスを継続利用できます。

    トークンリフレッシュの流れ:
        1. アクセストークンの有効期限切れを検出
        2. リフレッシュトークンを使用して /api/v1/auth/refresh エンドポイントを呼び出し
        3. 新しいアクセストークンとリフレッシュトークンのペアを取得
        4. 古いトークンを破棄し、新しいトークンで認証を継続

    処理フロー:
        1. ペイロードデータをコピー
        2. 有効期限を計算（デフォルトは30日）
        3. type="refresh"を設定してリフレッシュトークンであることを明示
        4. SECRET_KEYで署名してJWTトークンを生成

    Args:
        data (dict): トークンに含めるデータ。通常は{"sub": "user_id"}形式。
                    アクセストークンと同じユーザー情報を含めます。
        expires_delta (Optional[timedelta], optional): トークンの有効期限。
                    指定しない場合はデフォルトの30日を使用。
                    アクセストークンより長い期間を設定するのが一般的です。

    Returns:
        str: エンコードされたJWTリフレッシュトークン文字列。
             形式はアクセストークンと同じですが、type="refresh"が含まれます。

    Examples:
        >>> # 通常の使用（デフォルトの30日有効期限）
        >>> refresh_token = create_refresh_token(data={"sub": "123"})

        >>> # カスタムの有効期限（例: 7日間）
        >>> from datetime import timedelta
        >>> refresh_token = create_refresh_token(
        ...     data={"sub": "123"},
        ...     expires_delta=timedelta(days=7)
        ... )

    Note:
        - リフレッシュトークンはアクセストークンより慎重に扱う必要があります
        - HTTPOnlyクッキーに保存することでXSS攻撃から保護します
        - リフレッシュトークンが漏洩した場合、長期間不正アクセスされる可能性があります

    セキュリティ:
        - リフレッシュトークンは必ずHTTPOnlyクッキーに保存してください
        - ローテーション戦略: 新しいリフレッシュトークンを発行時に古いトークンを無効化
        - リフレッシュトークンの使用は厳密にログに記録することを推奨
    """
    import logging

    logger = logging.getLogger(__name__)

    # ペイロードデータのコピーを作成
    to_encode = data.copy()

    # 有効期限の計算
    if expires_delta:
        # カスタムの有効期限が指定された場合
        expire = datetime.utcnow() + expires_delta
    else:
        # リフレッシュトークンはアクセストークンより長い有効期限を設定
        # デフォルト: 30日（アクセストークンの15分と比べて非常に長い）
        # ユーザーは1ヶ月間再ログインせずにサービスを利用可能
        expire = datetime.utcnow() + timedelta(days=30)

    # JWT標準クレームとカスタムクレームを追加
    # exp: 有効期限（UNIX timestamp）
    # type: "refresh" - リフレッシュトークンであることを識別
    #       この識別により、アクセストークンとリフレッシュトークンを区別し
    #       適切なエンドポイントでのみ使用可能にします
    to_encode.update({"exp": expire, "type": "refresh"})
    logger.debug(f"Creating refresh token with payload: {to_encode}, expire: {expire}")

    # JWTトークンをエンコード（署名付き）
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created refresh token: {encoded_jwt[:20]}...")
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    JWTトークンをデコードして検証します

    この関数はJWTトークンの署名を検証し、ペイロードを取り出します。
    トークンの改ざんや有効期限切れを自動的に検出します。

    処理フロー:
        1. トークン文字列をBase64デコード
        2. SECRET_KEYで署名を検証（改ざん検出）
        3. 有効期限(exp)をチェック
        4. ペイロードを返す

    Args:
        token (str): エンコードされたJWTトークン文字列。
                    形式: "header.payload.signature"

    Returns:
        dict: デコードされたペイロード。
              例: {"sub": "123", "exp": 1234567890, "type": "access"}

    Raises:
        HTTPException: 以下の場合に401 Unauthorizedエラーを返します:
            - トークンの署名が無効な場合（改ざんされている）
            - トークンの有効期限が切れている場合
            - トークンの形式が不正な場合
            - SECRET_KEYが一致しない場合

    Examples:
        >>> token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        >>> payload = decode_token(token)
        >>> print(payload["sub"])  # ユーザーID
        "123"

    Note:
        - この関数はトークンの有効性を検証しますが、
          ユーザーがデータベースに存在するかは確認しません
        - トークンのタイプ（access/refresh）の検証は呼び出し側で行います

    セキュリティ:
        - 署名検証により、トークンの改ざんを検出
        - 有効期限チェックにより、古いトークンの使用を防止
        - エラー時は詳細情報を漏らさないよう汎用的なメッセージを返す
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Decoding token: {token[:20]}...")

        # JWTトークンをデコードして検証
        # jwt.decode()は以下を自動的に実行します:
        # 1. 署名の検証（settings.SECRET_KEYを使用）
        # 2. 有効期限(exp)のチェック
        # 3. トークン形式の検証
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"Decoded payload: {payload}")
        return payload
    except JWTError as e:
        # JWTエラー（署名不正、有効期限切れ、形式エラーなど）
        logger.debug(f"JWT decode error: {str(e)}")

        # セキュリティ上、詳細なエラー情報は返さない
        # 攻撃者にトークンの状態を知られないようにするため
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証情報です",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """
    現在のユーザーを取得します（オプショナル認証）

    この関数はFastAPIの依存性注入（Depends）として使用され、
    リクエストからユーザーを特定しますが、認証が必須ではありません。
    認証されていない場合はNoneを返すため、公開エンドポイントと
    認証済みユーザーで動作が変わるエンドポイントで使用できます。

    認証フロー:
        1. Authorizationヘッダーからトークンを取得（Bearer形式）
        2. ヘッダーにない場合、Cookieからトークンを取得（フロントエンド用）
        3. トークンがない場合、Noneを返す（エラーにしない）
        4. トークンがある場合、デコードしてユーザーIDを取得
        5. データベースからユーザーを検索して返す

    トークン取得の優先順位:
        1. Authorizationヘッダー（API用、モバイルアプリ用）
        2. HTTPOnlyクッキー（Webフロントエンド用、XSS対策）

    Args:
        request (Request): FastAPIリクエストオブジェクト。
                          ヘッダーとクッキーの両方にアクセスするために必要。
        token (Optional[str]): Authorizationヘッダーから自動抽出されたトークン。
                              oauth2_schemeによって"Bearer <token>"形式から
                              トークン部分のみが抽出されます。
        db (Session): SQLAlchemyのデータベースセッション。
                     get_db依存性注入によって自動的に提供されます。

    Returns:
        Optional[User]: 認証に成功した場合はUserオブジェクト、
                       トークンがない、または無効な場合はNone。

    Examples:
        >>> # エンドポイントでの使用（認証オプショナル）
        >>> @router.get("/posts")
        >>> async def get_posts(current_user: Optional[User] = Depends(get_current_user)):
        >>>     if current_user:
        >>>         # 認証済みユーザー向けのコンテンツ
        >>>         return get_personalized_posts(current_user)
        >>>     else:
        >>>         # 公開コンテンツ
        >>>         return get_public_posts()

    Note:
        - この関数は認証エラーを投げません（オプショナル認証）
        - 認証を必須にしたい場合は get_current_active_user() を使用してください
        - ユーザーのis_activeフラグはチェックしません（それは別の関数で行います）

    セキュリティ:
        - Cookieは"auth_token"という名前で保存されている必要があります
        - トークンのデコードエラーはログに記録されますが、例外は投げられません
        - 無効なトークンは単にNoneを返すため、攻撃者に情報を漏らしません
    """
    import logging

    logger = logging.getLogger(__name__)

    # デバッグ情報のログ出力（開発時のトラブルシューティング用）
    logger.debug(f"Authorization header token: {token}")
    logger.debug(f"Cookies: {request.cookies}")

    # まずAuthorizationヘッダーからトークンを取得（優先）
    # API クライアント（モバイルアプリなど）はヘッダーを使用
    if not token:
        # ヘッダーにない場合、Cookieからトークンを取得
        # Webブラウザのフロントエンドはクッキーを使用（XSS対策のためHTTPOnly）
        token = request.cookies.get("auth_token")
        logger.debug(f"Token from cookie: {token}")

    # トークンが見つからない場合
    if not token:
        logger.debug("No token found in header or cookie")
        # エラーを投げずにNoneを返す（オプショナル認証のため）
        return None

    try:
        # トークンをデコードして検証
        payload = decode_token(token)
        logger.debug(f"Decoded payload: {payload}")

        # ペイロードから"sub"（subject）クレームを取得
        # "sub"はJWT標準でユーザーIDを表すフィールド
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.debug("No 'sub' in payload")
            # subがない場合は不正なトークン形式
            return None
    except HTTPException as e:
        # トークンのデコードエラー（期限切れ、署名不正など）
        logger.debug(f"Token decode error: {e.detail}")
        # エラーを投げずにNoneを返す（オプショナル認証のため）
        return None

    # データベースからユーザーを検索
    # user_idは文字列として保存されているため、intに変換
    user = db.query(User).filter(User.id == int(user_id)).first()
    logger.debug(f"User found: {user.id if user else None}")

    # ユーザーが存在すればそのまま返す、存在しなければNone
    # （トークンは有効だがユーザーが削除されている場合など）
    return user


async def get_current_active_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """
    現在のアクティブユーザーを取得します（認証必須）

    この関数は get_current_user() に依存し、認証を必須とします。
    ユーザーが認証されていない、またはアカウントが非アクティブな場合は
    HTTPExceptionを投げるため、保護されたエンドポイントで使用します。

    認証チェックの流れ:
        1. get_current_user()を呼び出してユーザーを取得
        2. ユーザーがNone（未認証）の場合、401エラー
        3. ユーザーのis_activeフラグをチェック
        4. 非アクティブの場合、400エラー
        5. すべてのチェックを通過したユーザーを返す

    Args:
        current_user (Optional[User]): get_current_user()から取得したユーザー。
                                       Depends依存性注入により自動的に提供されます。

    Returns:
        User: 認証済みかつアクティブなユーザーオブジェクト。
              この関数が正常に返る場合、ユーザーは必ず存在しアクティブです。

    Raises:
        HTTPException (401 Unauthorized): ユーザーが認証されていない場合。
            - トークンがない
            - トークンが無効
            - トークンの有効期限切れ
            - ユーザーがデータベースに存在しない

        HTTPException (400 Bad Request): ユーザーが非アクティブな場合。
            - 管理者によってアカウントが無効化されている
            - アカウント削除済み（論理削除）

    Examples:
        >>> # 保護されたエンドポイントでの使用（認証必須）
        >>> @router.get("/me")
        >>> async def get_my_profile(
        ...     current_user: User = Depends(get_current_active_user)
        ... ):
        ...     # current_userは必ず認証済みアクティブユーザー
        ...     return {"username": current_user.username}

        >>> # データ変更エンドポイントでの使用
        >>> @router.put("/profile")
        >>> async def update_profile(
        ...     profile_data: ProfileUpdate,
        ...     current_user: User = Depends(get_current_active_user)
        ... ):
        ...     # 認証済みユーザーのみプロフィール更新可能
        ...     return update_user_profile(current_user, profile_data)

    Note:
        - この関数を使用するエンドポイントは認証が必須です
        - 認証をオプショナルにしたい場合は get_current_user() を直接使用してください
        - スーパーユーザー権限が必要な場合は get_current_active_superuser() を使用してください

    セキュリティ:
        - 未認証アクセスを確実にブロック
        - 非アクティブなユーザーのアクセスを制限
        - WWW-Authenticateヘッダーを返してOAuth2仕様に準拠
    """
    # ユーザーが認証されているかチェック
    if not current_user:
        # get_current_user()がNoneを返した場合（未認証）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},  # OAuth2標準ヘッダー
        )

    # ユーザーがアクティブかチェック
    if not current_user.is_active:
        # アカウントが無効化されている場合
        # 理由: 管理者による無効化、利用規約違反、アカウント削除など
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非アクティブなユーザーです")

    # すべてのチェックを通過したアクティブユーザーを返す
    return current_user


async def get_current_active_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    現在のスーパーユーザーを取得します（管理者権限必須）

    この関数は管理者専用エンドポイントで使用され、スーパーユーザー権限を持つ
    ユーザーのみアクセスを許可します。システム管理、ユーザー管理、
    設定変更などの重要な操作に使用します。

    権限チェックの流れ:
        1. get_current_active_user()で認証済みアクティブユーザーを取得
        2. ユーザーのis_superuserフラグをチェック
        3. スーパーユーザーでない場合、403エラー
        4. スーパーユーザーであればユーザーを返す

    Args:
        current_user (User): get_current_active_user()から取得したユーザー。
                            この時点で既に認証済みかつアクティブが保証されています。

    Returns:
        User: スーパーユーザー権限を持つユーザーオブジェクト。

    Raises:
        HTTPException (403 Forbidden): ユーザーがスーパーユーザーでない場合。
            一般ユーザーが管理者専用エンドポイントにアクセスしようとした場合に発生。

    Examples:
        >>> # 管理者専用エンドポイント（全ユーザー一覧取得）
        >>> @router.get("/admin/users")
        >>> async def list_all_users(
        ...     current_user: User = Depends(get_current_active_superuser),
        ...     db: Session = Depends(get_db)
        ... ):
        ...     # スーパーユーザーのみアクセス可能
        ...     return db.query(User).all()

        >>> # ユーザー削除エンドポイント
        >>> @router.delete("/admin/users/{user_id}")
        >>> async def delete_user(
        ...     user_id: int,
        ...     current_user: User = Depends(get_current_active_superuser),
        ...     db: Session = Depends(get_db)
        ... ):
        ...     # 管理者のみユーザー削除可能
        ...     user = db.query(User).get(user_id)
        ...     db.delete(user)
        ...     db.commit()

    Note:
        - この関数は最高レベルの権限チェックです
        - スーパーユーザーフラグはデータベースのUserテーブルで管理
        - プロジェクト単位の権限管理にはPermissionCheckerを使用してください

    セキュリティ:
        - 管理者機能への不正アクセスを防止
        - 403 Forbiddenで権限不足を明示（401 Unauthorizedとは区別）
        - スーパーユーザー権限の変更はデータベース操作でのみ可能
    """
    # スーパーユーザー権限をチェック
    if not current_user.is_superuser:
        # スーパーユーザーでない場合は403エラー
        # 401（未認証）ではなく403（権限不足）を返すことで、
        # 「認証はされているが権限がない」ことを明示
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="権限が不足しています")

    # スーパーユーザーであることが確認されたユーザーを返す
    return current_user


def verify_refresh_token(token: str) -> bool:
    """
    リフレッシュトークンの有効性を検証します

    この関数はリフレッシュトークンが正しい形式で、有効期限内であり、
    type="refresh"であることを確認します。トークンリフレッシュエンドポイントで
    使用され、アクセストークンとリフレッシュトークンを区別します。

    検証項目:
        1. JWT形式が正しいか
        2. 署名が有効か（改ざん検出）
        3. 有効期限が切れていないか
        4. type="refresh"であるか（アクセストークンとの区別）

    Args:
        token (str): 検証するリフレッシュトークン文字列。

    Returns:
        bool: トークンが有効なリフレッシュトークンの場合True、
              それ以外（無効、期限切れ、type不一致）の場合False。

    Examples:
        >>> # リフレッシュトークンの検証
        >>> token = request.cookies.get("refresh_token")
        >>> if verify_refresh_token(token):
        ...     # 新しいトークンペアを発行
        ...     new_access_token = create_access_token({"sub": user_id})
        ...     new_refresh_token = create_refresh_token({"sub": user_id})
        ... else:
        ...     # 再ログインが必要
        ...     raise HTTPException(401, "リフレッシュトークンが無効です")

    Note:
        - この関数は例外を投げず、bool値を返します
        - 詳細なエラー情報が必要な場合はdecode_token()を使用してください
        - アクセストークンを渡すとtype不一致でFalseを返します

    セキュリティ:
        - type="refresh"チェックにより、アクセストークンの誤用を防止
        - リフレッシュエンドポイントでのアクセストークン使用を防ぐ
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # JWTトークンをデコードして検証
        # 署名検証と有効期限チェックが自動的に行われる
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # リフレッシュトークンであることを確認
        # アクセストークンがリフレッシュエンドポイントで使用されることを防ぐ
        if payload.get("type") != "refresh":
            logger.debug("Token is not a refresh token")
            return False

        # すべてのチェックを通過
        return True
    except JWTError as e:
        # JWTエラー（期限切れ、署名不正、形式エラーなど）
        logger.debug(f"Refresh token verification failed: {str(e)}")
        return False


async def get_current_user_with_refresh_token(
    request: Request, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    リフレッシュトークンから現在のユーザーを取得します

    この関数はトークンリフレッシュエンドポイント専用で、
    リフレッシュトークンを使用してユーザーを認証します。
    アクセストークンの期限が切れた際に、新しいトークンペアを発行するために使用されます。

    処理フロー:
        1. Cookieまたはヘッダーからリフレッシュトークンを取得
        2. トークンをデコードして検証
        3. type="refresh"であることを確認（セキュリティチェック）
        4. ユーザーIDを取得
        5. データベースからユーザーを検索
        6. ユーザーがアクティブであることを確認
        7. ユーザーを返す

    トークン取得の優先順位:
        1. Cookie: "refresh_token"（Webフロントエンド用）
        2. Authorizationヘッダー（API/モバイル用）

    Args:
        request (Request): FastAPIリクエストオブジェクト。
                          Cookieからリフレッシュトークンを取得するために使用。
        token (Optional[str]): Authorizationヘッダーから自動抽出されたトークン。
                              Cookieにない場合のフォールバック。
        db (Session): SQLAlchemyのデータベースセッション。

    Returns:
        User: 認証済みアクティブユーザーオブジェクト。
              新しいトークンペアを発行するために使用されます。

    Raises:
        HTTPException (401 Unauthorized): 以下の場合に発生:
            - リフレッシュトークンがない
            - トークンが無効（署名不正、期限切れ）
            - type="refresh"でない（アクセストークンが渡された）
            - トークンにuser IDがない

        HTTPException (404 Not Found): ユーザーがデータベースに存在しない場合。
            トークンは有効だがユーザーが削除されている場合に発生。

        HTTPException (400 Bad Request): ユーザーが非アクティブな場合。
            アカウントが無効化されている場合に発生。

    Examples:
        >>> # トークンリフレッシュエンドポイント
        >>> @router.post("/auth/refresh")
        >>> async def refresh_tokens(
        ...     current_user: User = Depends(get_current_user_with_refresh_token)
        ... ):
        ...     # リフレッシュトークンが有効な場合、新しいトークンペアを発行
        ...     access_token = create_access_token({"sub": str(current_user.id)})
        ...     refresh_token = create_refresh_token({"sub": str(current_user.id)})
        ...
        ...     response = JSONResponse({"access_token": access_token})
        ...     response.set_cookie("auth_token", access_token, httponly=True)
        ...     response.set_cookie("refresh_token", refresh_token, httponly=True)
        ...     return response

    Note:
        - この関数はトークンリフレッシュエンドポイント専用です
        - 通常のAPIエンドポイントでは get_current_active_user() を使用してください
        - リフレッシュトークンはアクセストークンより長期間有効です

    セキュリティ:
        - type="refresh"チェックでアクセストークンの誤用を防止
        - リフレッシュトークンの使用を厳密に制限
        - トークンリフレッシュ時は新しいリフレッシュトークンも発行（ローテーション）
        - 詳細なエラー情報を返さず、攻撃者に情報を漏らさない
    """
    import logging

    logger = logging.getLogger(__name__)

    # まずCookieからリフレッシュトークンを取得（Webフロントエンド用）
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        # Cookieにない場合、Authorizationヘッダーから取得（API/モバイル用）
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="リフレッシュトークンが必要です",
                headers={"WWW-Authenticate": "Bearer"},
            )
        refresh_token = token

    try:
        # トークンをデコードして検証
        payload = decode_token(refresh_token)

        # リフレッシュトークンであることを確認
        # この確認により、アクセストークンがリフレッシュエンドポイントで
        # 使用されることを防ぎます（セキュリティ重要）
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンタイプです",
            )

        # ユーザーIDを取得
        user_id: str = payload.get("sub")
        if user_id is None:
            # subがない場合は不正なトークン形式
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです",
            )
    except HTTPException:
        # HTTPExceptionはそのまま再送出
        raise

    # データベースからユーザーを検索
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        # トークンは有効だがユーザーが存在しない
        # （ユーザー削除後にトークンが使用された場合など）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # ユーザーがアクティブであることを確認
    if not user.is_active:
        # 非アクティブなユーザーはトークンリフレッシュ不可
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="非アクティブなユーザーです")

    # すべてのチェックを通過したユーザーを返す
    # 呼び出し側で新しいトークンペアを発行
    return user
