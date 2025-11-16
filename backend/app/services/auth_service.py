"""
認証サービス - OAuth2.0認証フロー管理モジュール

このモジュールは、Backlog OAuth2.0認証フローの全体を管理し、
以下の責任を担います：
1. OAuth2.0の標準的な認証フロー（Authorization Code Grant）の実装
2. セキュリティを考慮したState管理とCSRF攻撃対策
3. トークン交換とユーザー情報取得の統合
4. ユーザーの新規作成・更新処理
5. JWT認証トークンの発行
6. ロールベースアクセス制御（RBAC）の初期設定

OAuth2.0フローの概要：
1. クライアント（フロントエンド）が認証URLにユーザーをリダイレクト
2. ユーザーがBacklogで認証し、許可を与える
3. Backlogが認可コード（code）とstateパラメータをコールバックURLに送信
4. このサービスがstateを検証し、codeをアクセストークンに交換
5. アクセストークンを使用してユーザー情報を取得
6. ユーザーをデータベースに保存し、JWTトークンを発行

セキュリティ上の重要な考慮事項：
- State パラメータによるCSRF攻撃の防止
- トークンの安全な保存と更新
- 適切なエラーハンドリングによる情報漏洩の防止
- ロールベースの権限管理

使用例：
    auth_service = AuthService(backlog_oauth_service)

    # OAuth認証フロー
    oauth_state = auth_service.validate_oauth_state(db, state)
    token_data = await auth_service.exchange_code_for_token(code, space_key)
    user_info = await auth_service.get_backlog_user_info(access_token, space_key)
    user = auth_service.find_or_create_user(db, user_info)
    access_token, refresh_token = auth_service.create_jwt_tokens(user.id)
"""

from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import logging
import json
import base64
import secrets

from app.models.user import User
from app.models.auth import OAuthState, OAuthToken
from app.models.rbac import Role, UserRole
from app.core.exceptions import ValidationException, NotFoundException
from app.core.security import create_access_token, create_refresh_token
from app.services.backlog_oauth import BacklogOAuthService
from app.core.utils import QueryBuilder
from app.core.config import settings
from app.services.auth_validator import BacklogAuthValidator

logger = logging.getLogger(__name__)


class AuthService:
    """
    認証サービスクラス

    OAuth2.0認証フローの実装と、ユーザー認証・認可に関する
    ビジネスロジックを提供します。

    主要な機能：
    - OAuth2.0 State パラメータの生成と検証（CSRF対策）
    - 認可コードのアクセストークンへの交換
    - Backlog APIを通じたユーザー情報の取得
    - ユーザーの作成・更新処理
    - OAuthトークンの安全な保存
    - デフォルトロール（MEMBER）の割り当て
    - JWT認証トークン（Access Token / Refresh Token）の発行

    Attributes:
        backlog_oauth_service (BacklogOAuthService): Backlog OAuth2.0操作を行うサービス

    セキュリティ考慮事項：
        - State パラメータは暗号学的に安全な乱数で生成される
        - State の有効期限は10分間（デフォルト）
        - トークンは暗号化してデータベースに保存される
        - 不正なstateによるCSRF攻撃を防止する

    使用例：
        >>> auth_service = AuthService(backlog_oauth_service)
        >>> # State検証
        >>> oauth_state = auth_service.validate_oauth_state(db, state="abc123")
        >>> # トークン交換
        >>> token_data = await auth_service.exchange_code_for_token(code="xyz", space_key="myspace")
        >>> # ユーザー作成
        >>> user = auth_service.find_or_create_user(db, user_info)
        >>> # JWTトークン生成
        >>> access_token, refresh_token = auth_service.create_jwt_tokens(user.id)
    """

    def __init__(self, backlog_oauth_service: BacklogOAuthService):
        """
        認証サービスの初期化

        Args:
            backlog_oauth_service (BacklogOAuthService):
                Backlog OAuth2.0サービスのインスタンス。
                実際のBacklog APIとの通信を担当する。

        Note:
            依存性注入パターンを使用しているため、テスト時には
            モックオブジェクトを渡すことができます。
        """
        self.backlog_oauth_service = backlog_oauth_service

    def validate_oauth_state(self, db: Session, state: str) -> OAuthState:
        """
        OAuth2.0のstateパラメータを検証し、CSRF攻撃を防止

        OAuth2.0の認証フローにおいて、stateパラメータは以下の目的で使用されます：
        1. CSRF（Cross-Site Request Forgery）攻撃の防止
        2. 認証リクエストとコールバックの紐付け
        3. 追加のメタデータ（space_keyなど）の受け渡し

        検証プロセス：
        1. データベースに保存されているstateと一致するか確認
        2. stateの有効期限（通常10分）が切れていないか確認
        3. 有効期限切れのstateは自動的に削除される

        セキュリティ上の重要性：
        - stateが一致しない場合、第三者による不正な認証試行の可能性がある
        - 同じstateは一度しか使用できない（リプレイ攻撃の防止）
        - 有効期限により、古いstateの悪用を防ぐ

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            state (str): Backlogから返されたstateパラメータ
                         （通常は暗号学的に安全な乱数文字列）

        Returns:
            OAuthState: 検証済みのOAuthStateオブジェクト
                        created_at, expires_at, space_keyなどの情報を含む

        Raises:
            ValidationException: 以下の場合に発生
                - stateがデータベースに存在しない（不正なリクエスト）
                - stateの有効期限が切れている

        Example:
            >>> oauth_state = auth_service.validate_oauth_state(db, "abc123def456")
            >>> print(f"Space: {oauth_state.space_key}")
            >>> print(f"Created: {oauth_state.created_at}")
        """
        # データベースから該当するstateを検索
        oauth_state = db.query(OAuthState).filter(OAuthState.state == state).first()

        # stateが存在しない場合はCSRF攻撃の可能性
        if not oauth_state:
            logger.error(f"無効なstateパラメータ - state: {state}")
            # デバッグ用：現在保存されているすべてのstateを確認
            # 本番環境では削除することを推奨（情報漏洩のリスク）
            all_states = db.query(OAuthState).all()
            logger.debug(f"現在のstate一覧: {[s.state for s in all_states]}")
            raise ValidationException(detail="無効なstateパラメータです")

        # stateの有効期限をチェック
        if oauth_state.is_expired():
            logger.error(f"stateパラメータの有効期限切れ - state: {state}")
            # 期限切れのstateは削除してデータベースをクリーンに保つ
            db.delete(oauth_state)
            db.commit()
            raise ValidationException(detail="stateパラメータの有効期限が切れています")

        return oauth_state

    def extract_space_key_from_state(self, state: str) -> str:
        """
        stateパラメータからBacklogスペースキーを抽出

        このメソッドは、マルチテナント対応のために、stateパラメータに
        エンコードされたspace_keyを抽出します。

        実装の詳細：
        1. stateパラメータはBase64でエンコードされたJSON文字列
        2. デコード後、JSON形式で"space_key"フィールドを取得
        3. 旧形式（単純な文字列）の場合は環境変数のデフォルト値を使用

        エンコード形式の例：
            元データ: {"space_key": "mycompany", "timestamp": 1234567890}
            Base64エンコード後: eyJzcGFjZV9rZXkiOiJteWNvbXBhbnkiLCAidGltZXN0YW1wIjogMTIzNDU2Nzg5MH0=

        後方互換性：
        - 古いバージョンでは単純な乱数文字列を使用していた
        - デコードに失敗した場合は環境変数のデフォルト値を返す

        Args:
            state (str): Base64エンコードされたJSON文字列、
                        または旧形式の単純な文字列

        Returns:
            str: Backlogスペースキー（例: "mycompany"）
                 デコードに失敗した場合は環境変数のデフォルト値

        Example:
            >>> # 新形式のstate
            >>> space_key = auth_service.extract_space_key_from_state("eyJzcGFjZV9rZXki...")
            >>> print(space_key)  # "mycompany"
            >>> # 旧形式のstate（デコード失敗）
            >>> space_key = auth_service.extract_space_key_from_state("random_string_123")
            >>> print(space_key)  # settings.BACKLOG_SPACE_KEY
        """
        try:
            # Base64デコード（URLセーフなエンコーディングを使用）
            state_json = base64.urlsafe_b64decode(state.encode()).decode()
            # JSON文字列をパース
            state_data = json.loads(state_json)
            # space_keyを取得（存在しない場合はデフォルト値）
            space_key = state_data.get("space_key", settings.BACKLOG_SPACE_KEY)
            logger.info(f"stateからspace_keyを取得 - space_key: {space_key}")
            return space_key
        except Exception as e:
            # デコードに失敗した場合は旧形式の可能性がある
            logger.warning(f"stateのデコードに失敗（旧形式の可能性）: {str(e)}")
            # 旧形式のstateの場合は環境変数のデフォルト値を使用
            return settings.BACKLOG_SPACE_KEY

    async def exchange_code_for_token(self, code: str, space_key: str) -> dict:
        """
        OAuth2.0認可コードをアクセストークンに交換

        OAuth2.0フローの重要なステップで、Backlogから受け取った一時的な
        認可コード（authorization code）を、実際にAPI呼び出しに使用できる
        アクセストークンとリフレッシュトークンに交換します。

        トークン交換の流れ：
        1. 認可コードとclient_id、client_secretをBacklogのトークンエンドポイントに送信
        2. Backlogが認可コードの有効性を検証
        3. 有効な場合、以下を含むトークン情報を返す：
           - access_token: API呼び出しに使用（有効期限あり）
           - refresh_token: アクセストークン更新に使用
           - expires_in: アクセストークンの有効期限（秒）
           - token_type: トークンタイプ（通常は "Bearer"）

        セキュリティ考慮事項：
        - 認可コードは1回のみ使用可能（リプレイ攻撃防止）
        - 認可コードの有効期限は通常10分程度
        - client_secretは安全に管理する必要がある
        - HTTPS通信必須（中間者攻撃の防止）

        Args:
            code (str): Backlogから受け取った認可コード
                       URLパラメータ"code"の値
            space_key (str): Backlogスペースキー（例: "mycompany"）

        Returns:
            dict: トークン情報を含む辞書
                {
                    "access_token": "eyJ...",
                    "refresh_token": "abc...",
                    "expires_in": 3600,
                    "token_type": "Bearer"
                }

        Raises:
            ExternalAPIException: 以下の場合に発生
                - 認可コードが無効または期限切れ
                - ネットワークエラー
                - Backlog APIのエラーレスポンス

        Example:
            >>> token_data = await auth_service.exchange_code_for_token(
            ...     code="abc123def456",
            ...     space_key="mycompany"
            ... )
            >>> print(token_data["access_token"])
        """
        logger.info("認証コードをアクセストークンに交換中...")
        return await self.backlog_oauth_service.exchange_code_for_token(code, space_key=space_key)

    async def get_backlog_user_info(self, access_token: str, space_key: str) -> dict:
        """
        Backlog APIからユーザー情報を取得し、アクセス権限を検証

        アクセストークンを使用してBacklog API（/users/myself）を呼び出し、
        認証したユーザーの詳細情報を取得します。

        取得される主な情報：
        - id: Backlogユーザーの一意な識別子
        - userId: ユーザーID文字列（ログイン名）
        - name: ユーザーの表示名
        - mailAddress: メールアドレス
        - roleType: ユーザーのロールタイプ（管理者、一般ユーザーなど）

        検証処理：
        1. スペースのアクセス権限検証
           - 許可されたスペースかどうかをチェック
           - マルチテナント環境での不正アクセスを防止
        2. ユーザーステータス検証
           - ユーザーがアクティブかどうか
           - 無効化されたユーザーのログインを防止

        セキュリティ考慮事項：
        - 不正なspace_keyによるアクセスをブロック
        - 無効化されたユーザーのアクセスをブロック
        - アクセストークンの有効性はBacklog APIが検証

        Args:
            access_token (str): Backlog APIアクセストークン
                               Bearer認証で使用される
            space_key (str): Backlogスペースキー
                            例: "mycompany"でhttps://mycompany.backlog.jp/にアクセス

        Returns:
            dict: ユーザー情報を含む辞書
                {
                    "id": 123456,
                    "userId": "john.doe",
                    "name": "John Doe",
                    "mailAddress": "john@example.com",
                    "roleType": 1,
                    ...
                }

        Raises:
            ExternalAPIException: Backlog APIの呼び出しに失敗した場合
                - アクセストークンが無効
                - ネットワークエラー
                - Backlogサーバーエラー
            ValidationException: アクセスが許可されていない場合
                - space_keyが許可リストに含まれていない
                - ユーザーが無効化されている

        Example:
            >>> user_info = await auth_service.get_backlog_user_info(
            ...     access_token="eyJ...",
            ...     space_key="mycompany"
            ... )
            >>> print(f"Welcome, {user_info['name']}!")
        """
        # スペースのアクセス権限を検証
        # 許可されたスペース以外からのアクセスをブロック
        BacklogAuthValidator.validate_space_access(space_key)

        logger.info("ユーザー情報を取得中...")
        # Backlog API（/users/myself）を呼び出し
        user_info = await self.backlog_oauth_service.get_user_info(access_token, space_key=space_key)

        # ユーザーの追加検証（ステータス確認など）
        BacklogAuthValidator.validate_user_status(user_info, space_key)

        return user_info

    def find_or_create_user(self, db: Session, user_info: dict) -> User:
        """
        Backlogユーザー情報を基にシステムユーザーを検索または新規作成

        Backlogから取得したユーザー情報を基に、データベース内でユーザーを検索します。
        見つからない場合は新規ユーザーとして登録し、既存の場合は情報を更新します。

        処理フロー：
        1. backlog_idでユーザーを検索
        2. 新規の場合：
           - Userモデルを作成
           - データベースに挿入
           - created_at、updated_atを設定
        3. 既存の場合：
           - email、name、userIdを最新情報で更新
           - updated_atを現在時刻に更新

        idempotent（冪等性）：
        - 同じユーザー情報で複数回呼び出しても安全
        - 既存ユーザーの場合は更新のみ実行

        データ同期の考慮事項：
        - Backlogでユーザー情報が変更された場合、次回ログイン時に自動的に同期される
        - emailがnullの場合は既存の値を保持（データ消失を防止）

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            user_info (dict): Backlog APIから取得したユーザー情報
                {
                    "id": 123456,           # backlog_id
                    "userId": "john.doe",   # ログインID
                    "name": "John Doe",     # 表示名
                    "mailAddress": "john@example.com"  # メールアドレス（オプション）
                }

        Returns:
            User: 作成または更新されたUserモデルのインスタンス
                  idフィールドはデータベースの主キー

        Example:
            >>> user_info = {"id": 123, "userId": "john", "name": "John Doe", "mailAddress": "john@example.com"}
            >>> user = auth_service.find_or_create_user(db, user_info)
            >>> print(f"User ID: {user.id}, Backlog ID: {user.backlog_id}")
            User ID: 1, Backlog ID: 123

        Note:
            - トランザクションは呼び出し側で管理される想定
            - 例外が発生した場合、データベースはロールバックされる
        """
        # backlog_idで既存ユーザーを検索
        user = db.query(User).filter(User.backlog_id == user_info["id"]).first()

        if not user:
            # 新規ユーザーの作成
            logger.info(f"新規ユーザーを作成 - backlog_id: {user_info['id']}")
            user = User(
                backlog_id=user_info["id"],
                email=user_info.get("mailAddress"),  # mailAddressがnullの可能性を考慮
                name=user_info["name"],
                user_id=user_info["userId"],
                is_active=True,  # デフォルトでアクティブ
                created_at=datetime.now(timezone.utc),  # UTC時刻で保存
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            db.commit()  # データベースに挿入
            db.refresh(user)  # 自動生成されたIDを取得
        else:
            logger.info(f"既存ユーザーを使用 - user_id: {user.id}")
            # 既存ユーザーの情報を最新化
            # Backlog側で情報が変更されている可能性があるため、常に更新
            user.email = user_info.get("mailAddress") or user.email  # nullの場合は既存値を保持
            user.name = user_info["name"]
            user.user_id = user_info["userId"]
            user.updated_at = datetime.now(timezone.utc)  # 最終更新日時を記録
            db.commit()

        return user

    def save_oauth_token(self, db: Session, user_id: int, token_data: dict, space_key: str, user_info: dict = None) -> None:
        """
        OAuthトークンをデータベースに安全に保存

        Backlogから取得したアクセストークンとリフレッシュトークンを
        データベースに保存します。トークンは暗号化して保存され、
        自動更新機能により継続的なAPI呼び出しが可能になります。

        保存される情報：
        - access_token: API呼び出しに使用（暗号化）
        - refresh_token: トークン更新に使用（暗号化）
        - expires_at: アクセストークンの有効期限
        - space_key: 対象のBacklogスペース
        - backlog_user_id: Backlogユーザー識別子
        - backlog_user_email: Backlogユーザーメールアドレス

        セキュリティ考慮事項：
        - トークンは暗号化してデータベースに保存
        - ユーザーごとに最新のトークンのみを保持（古いトークンは上書き）
        - 有効期限を記録し、自動更新のタイミングを判断

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            user_id (int): システム内部のユーザーID
            token_data (dict): Backlogから取得したトークン情報
                {
                    "access_token": "eyJ...",
                    "refresh_token": "abc...",
                    "expires_in": 3600,
                    "token_type": "Bearer"
                }
            space_key (str): Backlogスペースキー
            user_info (dict, optional): Backlogユーザー情報
                保存されたトークンに追加のメタデータを付与するために使用

        Returns:
            None

        Example:
            >>> token_data = {
            ...     "access_token": "eyJ...",
            ...     "refresh_token": "abc...",
            ...     "expires_in": 3600
            ... }
            >>> user_info = {"id": 123, "mailAddress": "john@example.com"}
            >>> auth_service.save_oauth_token(db, user_id=1, token_data=token_data,
            ...                               space_key="mycompany", user_info=user_info)

        Note:
            - トークンの暗号化はBacklogOAuthServiceで実装されている
            - 同じユーザーの既存トークンは上書きされる
        """
        # トークンを暗号化してデータベースに保存
        saved_token = self.backlog_oauth_service.save_token(db, user_id, token_data, space_key=space_key)

        # Backlogユーザー情報も保存（提供されている場合）
        # トークンとBacklogユーザーIDを紐付けることで、
        # 将来的なデバッグや監査に役立つ
        if user_info and saved_token:
            saved_token.backlog_user_id = str(user_info.get("id", ""))
            saved_token.backlog_user_email = user_info.get("mailAddress", "")
            db.commit()

    def assign_default_role_if_needed(self, db: Session, user: User) -> User:
        """
        新規ユーザーにデフォルトロール（MEMBER）を割り当て

        ロールベースアクセス制御（RBAC）の初期設定を行います。
        新規ユーザーにはデフォルトでMEMBERロールが付与され、
        基本的な機能へのアクセスが許可されます。

        ロール体系：
        - ADMIN: システム管理者（すべての権限）
        - TEAM_LEADER: チームリーダー（チーム管理権限）
        - MEMBER: 一般メンバー（基本機能のみ）

        処理フロー：
        1. ユーザーの現在のロール情報を取得
        2. ロールが未設定の場合のみ処理を実行
        3. MEMBERロールをデータベースから検索
        4. UserRoleレコードを作成（project_id=Nullでグローバルロール）
        5. ロール情報を再取得して返す

        グローバルロール vs プロジェクトロール：
        - グローバルロール: project_id=Null、システム全体で有効
        - プロジェクトロール: project_id指定、特定プロジェクト内でのみ有効

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            user (User): ロール割り当て対象のユーザーオブジェクト

        Returns:
            User: ロール情報を含むユーザーオブジェクト
                  user.user_rolesプロパティから割り当てられたロールにアクセス可能

        Example:
            >>> user = User(id=1, name="John Doe")
            >>> user_with_role = auth_service.assign_default_role_if_needed(db, user)
            >>> print(user_with_role.user_roles[0].role.name)
            MEMBER

        Note:
            - 既にロールが割り当てられている場合は何もしない
            - MEMBERロールが存在しない場合は割り当てをスキップ
            - QueryBuilder.with_user_roles()でEager Loadingを実行（N+1問題の回避）
        """
        # ユーザーのロール情報をEager Loadingで取得
        # Eager Loadingにより、後続の処理でN+1問題を回避
        user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == user.id)).first()

        # 新規ユーザー（ロール未設定）の場合、デフォルトロール（MEMBER）を割り当て
        if not user.user_roles:
            # MEMBERロールをデータベースから取得
            member_role = db.query(Role).filter(Role.name == "MEMBER").first()
            if member_role:
                # グローバルロールとしてMEMBERを割り当て
                user_role = UserRole(
                    user_id=user.id,
                    role_id=member_role.id,
                    project_id=None,  # Nullはグローバルロールを意味する
                    created_at=datetime.now(timezone.utc),
                )
                db.add(user_role)
                db.commit()
                db.refresh(user)
                # ロール情報を再取得して最新の状態を返す
                user = QueryBuilder.with_user_roles(db.query(User).filter(User.id == user.id)).first()

        return user

    def create_jwt_tokens(self, user_id: int) -> Tuple[str, str]:
        """
        JWT（JSON Web Token）認証トークンのペアを生成

        システム内部での認証に使用するJWTトークンを生成します。
        アクセストークンとリフレッシュトークンの2種類を発行し、
        セキュアでスケーラブルな認証を実現します。

        トークンの種類：
        1. アクセストークン（Access Token）
           - API呼び出しの認証に使用
           - 有効期限: 通常15〜60分（短め）
           - クレーム: {"sub": "user_id", "exp": expire_time}
           - セキュリティリスクを最小化するため短命

        2. リフレッシュトークン（Refresh Token）
           - アクセストークンの再発行に使用
           - 有効期限: 通常7〜30日（長め）
           - アクセストークン期限切れ時に新しいアクセストークンを取得
           - より長期間のセッション維持を可能にする

        JWT構造（例）：
        Header:  {"alg": "HS256", "typ": "JWT"}
        Payload: {"sub": "123", "exp": 1234567890}
        Signature: HMACSHA256(base64(header) + "." + base64(payload), secret)

        セキュリティ考慮事項：
        - トークンは署名されており改ざん検出が可能
        - subクレームにユーザーIDを含める（識別用）
        - expクレームで有効期限を管理
        - 秘密鍵は環境変数で安全に管理

        Args:
            user_id (int): トークンに埋め込むユーザーID
                          subクレームとして保存される

        Returns:
            Tuple[str, str]: (アクセストークン, リフレッシュトークン)のタプル
                例: ("eyJhbGc...", "eyJhbGc...")

        Example:
            >>> access_token, refresh_token = auth_service.create_jwt_tokens(user_id=123)
            >>> # フロントエンドに返す
            >>> return {
            ...     "access_token": access_token,
            ...     "refresh_token": refresh_token,
            ...     "token_type": "bearer"
            ... }

        Note:
            - トークンの有効期限は設定ファイルで調整可能
            - トークンはステートレス（サーバー側でセッション情報を保持しない）
            - ログアウト時はクライアント側でトークンを破棄する
        """
        # アクセストークンを生成（subクレームにユーザーIDを設定）
        access_token = create_access_token(data={"sub": str(user_id)})
        # リフレッシュトークンを生成
        refresh_token = create_refresh_token(data={"sub": str(user_id)})
        return access_token, refresh_token

    def cleanup_oauth_state(self, db: Session, oauth_state: OAuthState) -> None:
        """
        使用済みのOAuthStateレコードをデータベースから削除

        OAuth認証フローが正常に完了した後、使用済みのstateパラメータを
        データベースから削除します。これによりデータベースをクリーンに保ち、
        リプレイ攻撃を防止します。

        クリーンアップの重要性：
        1. セキュリティ: 同じstateの再利用を防止（リプレイ攻撃対策）
        2. パフォーマンス: 不要なレコードを削除しデータベースを最適化
        3. プライバシー: 認証フローの履歴を残さない

        呼び出しタイミング：
        - OAuth認証フローの最後のステップ
        - トークン交換とユーザー作成が成功した後
        - エラー時も期限切れのstateは自動削除される

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            oauth_state (OAuthState): 削除対象のOAuthStateオブジェクト

        Returns:
            None

        Example:
            >>> # OAuth認証フロー完了後
            >>> oauth_state = auth_service.validate_oauth_state(db, state)
            >>> # ... トークン交換、ユーザー作成などの処理 ...
            >>> auth_service.cleanup_oauth_state(db, oauth_state)

        Note:
            - トランザクション内で実行される
            - 削除に失敗してもアプリケーションの動作には影響しない
            - 期限切れのstateは自動的に削除される仕組みも別途存在
        """
        # 使用済みstateをデータベースから削除
        db.delete(oauth_state)
        # 変更をコミット
        db.commit()
