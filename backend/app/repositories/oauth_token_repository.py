"""
OAuthトークンリポジトリ - OAuth認証トークンデータアクセス層

このモジュールは、OAuthトークンモデルに特化したデータアクセスメソッドを提供します。

主要機能：
1. OAuthトークンの基本的なCRUD操作
2. ユーザーとプロバイダーによるトークン検索
3. トークンの有効期限チェック
4. 期限切れトークンの削除
5. トークンの最終使用日時の更新

パフォーマンス最適化：
- インデックスを活用した高速検索
- 複合条件による効率的なフィルタリング

使用例：
    oauth_repo = OAuthTokenRepository(db)

    # ユーザーのBacklogトークンを取得
    token = oauth_repo.get_user_token(user_id=1, provider="backlog")

    # トークンの最終使用日時を更新
    oauth_repo.update_last_used(token_id=1)

    # 期限切れトークンを削除
    oauth_repo.delete_expired_tokens()
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models.auth import OAuthToken
from app.repositories.base_repository import BaseRepository


class OAuthTokenRepository(BaseRepository[OAuthToken]):
    """
    OAuthトークンリポジトリクラス

    OAuthトークンモデルに対する専用のデータアクセスメソッドを提供します。
    BaseRepositoryの汎用メソッドに加え、トークン管理の特有機能を実装。

    主要メソッド：
    - get_user_token: ユーザーとプロバイダーでトークンを取得
    - get_user_tokens: ユーザーの全トークンを取得
    - get_by_provider: プロバイダーでトークンを取得
    - update_last_used: 最終使用日時を更新
    - delete_expired_tokens: 期限切れトークンを削除

    セキュリティ考慮：
    - トークンは暗号化して保存することを推奨
    - 定期的に期限切れトークンを削除
    """

    def __init__(self, db: Session):
        """
        OAuthTokenRepositoryの初期化

        Args:
            db (Session): SQLAlchemyのデータベースセッション
        """
        super().__init__(OAuthToken, db)

    def get_user_token(self, user_id: int, provider: str) -> Optional[OAuthToken]:
        """
        ユーザーとプロバイダーでトークンを取得

        特定のユーザーの特定プロバイダーのトークンを取得します。
        通常、ユーザーとプロバイダーの組み合わせは一意です。

        Args:
            user_id (int): ユーザーID
            provider (str): プロバイダー名（例: "backlog"）

        Returns:
            Optional[OAuthToken]:
                見つかった場合はOAuthTokenインスタンス、見つからない場合はNone

        Example:
            >>> token = oauth_repo.get_user_token(user_id=1, provider="backlog")
            >>> if token and not token.is_expired():
            ...     print(f"Access token: {token.access_token}")

        Note:
            - 複合インデックス（user_id, provider）による高速検索
            - ユーザー情報も取得する場合はget_user_token_with_userを使用
        """
        return self.db.query(OAuthToken).filter(OAuthToken.user_id == user_id, OAuthToken.provider == provider).first()

    def get_user_token_with_user(self, user_id: int, provider: str) -> Optional[OAuthToken]:
        """
        ユーザー情報を含めてトークンを取得（N+1問題対策）

        トークン情報とユーザー情報を1回のクエリで効率的に取得します。

        Args:
            user_id (int): ユーザーID
            provider (str): プロバイダー名（例: "backlog"）

        Returns:
            Optional[OAuthToken]:
                見つかった場合はユーザー情報を含むOAuthTokenインスタンス、
                見つからない場合はNone

        Example:
            >>> token = oauth_repo.get_user_token_with_user(
            ...     user_id=1, provider="backlog"
            ... )
            >>> if token:
            ...     print(f"User: {token.user.name}")
            ...     print(f"Token: {token.access_token}")

        Note:
            - token.userが事前ロード済み
            - 追加のクエリは発行されない
        """
        return (
            self.db.query(OAuthToken)
            .options(joinedload(OAuthToken.user))
            .filter(OAuthToken.user_id == user_id, OAuthToken.provider == provider)
            .first()
        )

    def get_user_tokens(self, user_id: int) -> List[OAuthToken]:
        """
        ユーザーの全トークンを取得

        特定のユーザーに紐づくすべてのOAuthトークンを取得します。
        複数のプロバイダーと連携している場合に使用します。

        Args:
            user_id (int): ユーザーID

        Returns:
            List[OAuthToken]: ユーザーのトークンリスト

        Example:
            >>> tokens = oauth_repo.get_user_tokens(user_id=1)
            >>> for token in tokens:
            ...     print(f"{token.provider}: {token.is_expired()}")

        Note:
            - プロバイダー名でソート
        """
        return self.db.query(OAuthToken).filter(OAuthToken.user_id == user_id).order_by(OAuthToken.provider).all()

    def get_by_provider(self, provider: str, skip: int = 0, limit: int = 100) -> List[OAuthToken]:
        """
        プロバイダーでトークンを取得

        特定のプロバイダーのすべてのトークンを取得します。
        管理者用の機能や統計情報の取得に使用します。

        Args:
            provider (str): プロバイダー名（例: "backlog"）
            skip (int, optional): スキップするレコード数。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100

        Returns:
            List[OAuthToken]: プロバイダーのトークンリスト

        Example:
            >>> backlog_tokens = oauth_repo.get_by_provider("backlog")
            >>> print(f"Total Backlog users: {len(backlog_tokens)}")

        Note:
            - 更新日時の降順でソート
        """
        return (
            self.db.query(OAuthToken)
            .filter(OAuthToken.provider == provider)
            .order_by(OAuthToken.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_expired_tokens(self, provider: Optional[str] = None) -> List[OAuthToken]:
        """
        期限切れトークンを取得

        有効期限が切れたトークンを取得します。
        定期的なクリーンアップ処理に使用します。

        Args:
            provider (Optional[str], optional):
                プロバイダーで絞り込み。Noneの場合は全プロバイダー

        Returns:
            List[OAuthToken]: 期限切れトークンのリスト

        Example:
            >>> # 全プロバイダーの期限切れトークン
            >>> expired = oauth_repo.get_expired_tokens()
            >>> print(f"Expired tokens: {len(expired)}")

            >>> # Backlogの期限切れトークンのみ
            >>> expired = oauth_repo.get_expired_tokens(provider="backlog")

        Note:
            - expires_atがNullのトークンは除外
            - 現在時刻より前の有効期限を持つトークンを取得
        """
        query = self.db.query(OAuthToken).filter(OAuthToken.expires_at.isnot(None), OAuthToken.expires_at < datetime.utcnow())

        # プロバイダーでフィルタリング
        if provider is not None:
            query = query.filter(OAuthToken.provider == provider)

        return query.all()

    def update_last_used(self, token_id: int) -> bool:
        """
        トークンの最終使用日時を更新

        トークンが使用されたときに、last_used_atを現在時刻に更新します。
        トークンの使用状況を追跡するために使用します。

        Args:
            token_id (int): トークンID

        Returns:
            bool: 更新成功時はTrue、トークンが存在しない場合はFalse

        Example:
            >>> if oauth_repo.update_last_used(token_id=1):
            ...     print("Last used timestamp updated")

        Note:
            - db.commit()は呼び出し側で実行
        """
        token = self.get(token_id)

        if token:
            token.last_used_at = datetime.utcnow()
            self.db.flush()
            return True

        return False

    def delete_expired_tokens(self, provider: Optional[str] = None) -> int:
        """
        期限切れトークンを削除

        有効期限が切れたトークンをデータベースから削除します。
        定期的なクリーンアップ処理として実行することを推奨します。

        Args:
            provider (Optional[str], optional):
                プロバイダーで絞り込み。Noneの場合は全プロバイダー

        Returns:
            int: 削除されたトークンの数

        Example:
            >>> # 全プロバイダーの期限切れトークンを削除
            >>> deleted_count = oauth_repo.delete_expired_tokens()
            >>> print(f"Deleted {deleted_count} expired tokens")

            >>> # Backlogの期限切れトークンのみ削除
            >>> deleted_count = oauth_repo.delete_expired_tokens(
            ...     provider="backlog"
            ... )

        Note:
            - db.commit()は呼び出し側で実行
            - 削除前にログやバックアップを取ることを推奨
        """
        query = self.db.query(OAuthToken).filter(OAuthToken.expires_at.isnot(None), OAuthToken.expires_at < datetime.utcnow())

        # プロバイダーでフィルタリング
        if provider is not None:
            query = query.filter(OAuthToken.provider == provider)

        # 削除前にカウント
        count = query.count()

        # 削除実行
        query.delete(synchronize_session=False)
        self.db.flush()

        return count

    def upsert_token(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        **kwargs,
    ) -> OAuthToken:
        """
        トークンをUPSERT（存在すれば更新、なければ作成）

        既存のトークンがあれば更新し、なければ新規作成します。
        OAuth認証のコールバック処理で使用します。

        Args:
            user_id (int): ユーザーID
            provider (str): プロバイダー名（例: "backlog"）
            access_token (str): アクセストークン
            refresh_token (Optional[str], optional):
                リフレッシュトークン。デフォルトはNone
            expires_at (Optional[datetime], optional):
                有効期限。デフォルトはNone
            **kwargs: その他のプロバイダー固有フィールド
                （例: backlog_space_key, backlog_user_id）

        Returns:
            OAuthToken: 作成または更新されたトークン

        Example:
            >>> token = oauth_repo.upsert_token(
            ...     user_id=1,
            ...     provider="backlog",
            ...     access_token="abc123",
            ...     refresh_token="xyz789",
            ...     expires_at=datetime.now() + timedelta(days=30),
            ...     backlog_space_key="myspace"
            ... )

        Note:
            - db.commit()は呼び出し側で実行
            - セキュリティのため、トークンは暗号化して保存することを推奨
        """
        # 既存のトークンを検索
        existing = self.get_user_token(user_id, provider)

        if existing:
            # 更新
            existing.access_token = access_token
            if refresh_token is not None:
                existing.refresh_token = refresh_token
            if expires_at is not None:
                existing.expires_at = expires_at

            # その他のフィールドを更新
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)

            existing.updated_at = datetime.utcnow()
            self.db.flush()
            self.db.refresh(existing)

            return existing
        else:
            # 新規作成
            token_data = {
                "user_id": user_id,
                "provider": provider,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
                **kwargs,
            }

            return self.create(token_data)
