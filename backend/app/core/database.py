"""
データベース関連のユーティリティ

このモジュールは、SQLAlchemyを使用したデータベース操作を簡素化し、
安全性を向上させるためのユーティリティ関数とクラスを提供します。

主要な機能:
    1. トランザクション管理
       - 自動コミット/ロールバック
       - コンテキストマネージャーによる安全な操作

    2. バッチ処理
       - 大量データの効率的な挿入
       - メモリ効率の良い処理

    3. ページネーション
       - リスト取得時の件数制限とオフセット

主要なクラス・関数:
    - transaction(): トランザクションコンテキストマネージャー
    - BatchProcessor: バッチ処理用クラス
    - paginate_query(): クエリにページネーションを適用

使用例:
    ```python
    from app.core.database import transaction, BatchProcessor
    from app.db.session import get_db

    # トランザクション管理
    db = next(get_db())
    with transaction(db) as session:
        user = User(username="test")
        session.add(user)
        # 自動的にcommit、エラー時は自動的にrollback

    # バッチ処理
    with BatchProcessor(db, batch_size=100) as processor:
        for item in large_dataset:
            processor.add(User(username=item))
        # 自動的にflush（残りのアイテムを保存）
    ```

データベース操作のベストプラクティス:
    - 必ずトランザクション内で操作を行う
    - 長時間実行されるクエリは避ける
    - N+1問題に注意（eager loading を使用）
    - バッチ処理で大量データを効率的に処理

セキュリティの考慮事項:
    - SQLインジェクション対策（SQLAlchemy ORMを使用）
    - トランザクション分離レベルの適切な設定
    - デッドロック検出とリトライ
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.core.exceptions import handle_database_error
import logging

logger = logging.getLogger(__name__)


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """
    トランザクションコンテキストマネージャー

    データベース操作を安全に実行するためのコンテキストマネージャーです。
    withブロック内でデータベース操作を行い、成功時は自動的にコミット、
    エラー時は自動的にロールバックします。

    トランザクションの動作:
        1. withブロックに入る: トランザクション開始
        2. withブロック内: データベース操作を実行
        3. withブロック正常終了: 自動的にcommit()を実行
        4. 例外発生時: 自動的にrollback()を実行してエラーを再送出
        5. 最終的に: セッションをclose()（finallyブロック）

    トランザクションの利点:
        - ACID特性の保証（原子性、一貫性、独立性、永続性）
        - 複数の操作をまとめて実行（全て成功または全て失敗）
        - エラー時の自動ロールバックでデータの整合性を保つ

    Args:
        db (Session): SQLAlchemyのデータベースセッション。
                     FastAPIの依存性注入（Depends(get_db)）で取得。

    Yields:
        Session: トランザクション内で使用するデータベースセッション。
                このセッションで行った変更は、withブロックを抜けると
                自動的にコミットされます。

    Raises:
        DatabaseException: データベースエラーが発生した場合。
                          handle_database_error()によって適切な例外に変換されます。

    Examples:
        >>> # 単一レコードの追加
        >>> db = next(get_db())
        >>> with transaction(db) as session:
        ...     user = User(username="alice", email="alice@example.com")
        ...     session.add(user)
        ... # ここで自動的にcommit

        >>> # 複数の関連操作（全て成功または全て失敗）
        >>> with transaction(db) as session:
        ...     user = User(username="bob")
        ...     session.add(user)
        ...     session.flush()  # IDを取得するため
        ...
        ...     profile = Profile(user_id=user.id, bio="Hello")
        ...     session.add(profile)
        ... # 両方の操作が成功した場合のみcommit

        >>> # エラー時の自動ロールバック
        >>> try:
        ...     with transaction(db) as session:
        ...         user = User(username="charlie")
        ...         session.add(user)
        ...         raise ValueError("Something went wrong")
        ... except DatabaseException:
        ...     # ロールバックは自動的に実行済み
        ...     print("Transaction rolled back")

    Note:
        - withブロック内で例外が発生すると、全ての変更がロールバックされます
        - 長時間実行されるトランザクションは避けてください（ロック問題）
        - ネストしたトランザクションは避けてください（セーブポイントが必要な場合は別途実装）
        - セッションは最終的に必ずclose()されます（リソースリーク防止）

    ベストプラクティス:
        - データベース操作は必ずこのコンテキストマネージャー内で実行
        - トランザクション内では最小限の操作のみを実行
        - 外部API呼び出しなど、時間のかかる処理はトランザクション外で実行
    """
    try:
        logger.debug("Starting database transaction")

        # withブロック内でセッションを使用可能にする
        yield db

        # withブロックが正常終了した場合、変更をコミット
        db.commit()
        logger.debug("Database transaction committed")
    except Exception as e:
        # エラーが発生した場合、変更を全てロールバック
        # これにより、データベースは操作前の状態に戻ります
        logger.error(f"Database transaction failed: {str(e)}")
        db.rollback()

        # エラーを適切な例外型に変換して再送出
        # handle_database_error()は、SQLAlchemyの例外を
        # アプリケーション固有の例外に変換します
        handle_database_error(e)
    finally:
        # 成功・失敗に関わらず、最終的にセッションをクローズ
        # これにより、データベース接続がリリースされます
        db.close()


class BatchProcessor:
    """
    バッチ処理用ユーティリティクラス

    大量のデータを効率的にデータベースに挿入するためのクラスです。
    個別にcommitするのではなく、指定したサイズごとにまとめて挿入することで、
    パフォーマンスを大幅に向上させます。

    動作の仕組み:
        1. add()でアイテムを内部バッファに追加
        2. バッファがbatch_sizeに達したら自動的にflush()
        3. flush()でbulk_save_objects()を使用して一括挿入
        4. コンテキストマネージャー終了時に残りのアイテムをflush()

    パフォーマンスの改善:
        - 個別のINSERT文ではなく、バルクINSERTを使用
        - トランザクション回数を削減（commit回数が減る）
        - メモリ使用量を制御（batch_sizeで調整可能）

    Attributes:
        db (Session): SQLAlchemyのデータベースセッション
        batch_size (int): 一度に挿入するアイテム数（デフォルト100）
        items (list): 挿入待ちのアイテムを保持するバッファ

    主要なメソッド:
        - add(item): アイテムをバッファに追加
        - flush(): バッファ内のアイテムを一括挿入

    使用例:
        ```python
        from app.core.database import BatchProcessor
        from app.db.session import get_db
        from app.models.user import User

        # コンテキストマネージャーとして使用（推奨）
        db = next(get_db())
        with BatchProcessor(db, batch_size=100) as processor:
            for i in range(1000):
                user = User(username=f"user_{i}")
                processor.add(user)
            # withブロックを抜けると自動的に残りをflush

        # 手動でflush
        processor = BatchProcessor(db)
        for i in range(50):
            processor.add(User(username=f"user_{i}"))
        processor.flush()  # 手動でflush
        ```

    Note:
        - bulk_save_objects()は自動的にIDを返さないことに注意
        - リレーションシップのある複雑なオブジェクトには向かない場合がある
        - 大量データの初期投入や、バッチジョブで使用するのが適切
    """

    def __init__(self, db: Session, batch_size: int = 100):
        """
        BatchProcessorを初期化します

        Args:
            db (Session): SQLAlchemyのデータベースセッション
            batch_size (int, optional): 一度に挿入するアイテム数。
                                       デフォルトは100。
                                       メモリとパフォーマンスのバランスを考慮して設定。

        Examples:
            >>> db = next(get_db())
            >>> # デフォルトのバッチサイズ（100）
            >>> processor = BatchProcessor(db)

            >>> # カスタムバッチサイズ
            >>> processor = BatchProcessor(db, batch_size=500)
        """
        self.db = db
        self.batch_size = batch_size
        self.items = []  # 挿入待ちアイテムのバッファ

    def add(self, item):
        """
        アイテムをバッチに追加します

        アイテムを内部バッファに追加し、バッファサイズがbatch_sizeに
        達した場合は自動的にflush()を呼び出してデータベースに挿入します。

        処理フロー:
            1. アイテムをitemsリストに追加
            2. itemsのサイズがbatch_size以上か確認
            3. batch_size以上の場合、自動的にflush()を実行

        Args:
            item: SQLAlchemyモデルのインスタンス（例: User, Project）

        Examples:
            >>> processor = BatchProcessor(db, batch_size=100)
            >>> for i in range(250):
            ...     user = User(username=f"user_{i}")
            ...     processor.add(user)
            ...     # 100件、200件のタイミングで自動的にflush
            >>> processor.flush()  # 残りの50件をflush

        Note:
            - flush()は自動的に呼ばれるため、通常は意識する必要はありません
            - 処理途中でエラーが発生した場合、それまでのバッチはコミット済みです
        """
        # アイテムをバッファに追加
        self.items.append(item)

        # バッファサイズがbatch_sizeに達したら自動的にflush
        if len(self.items) >= self.batch_size:
            self.flush()

    def flush(self):
        """
        バッファ内のアイテムを一括してデータベースに挿入します

        bulk_save_objects()を使用して、バッファ内の全アイテムを
        一度のクエリで効率的に挿入します。挿入後、バッファをクリアします。

        処理フロー:
            1. バッファが空かチェック（空なら何もしない）
            2. bulk_save_objects()で一括挿入
            3. commit()でトランザクションをコミット
            4. バッファをクリア
            5. エラー時は rollback() して例外を送出

        Raises:
            DatabaseException: データベースエラーが発生した場合

        Examples:
            >>> processor = BatchProcessor(db, batch_size=100)
            >>> for i in range(50):
            ...     processor.add(User(username=f"user_{i}"))
            >>> processor.flush()  # 50件を手動でflush

        Note:
            - バッファが空の場合は何もしません
            - エラーが発生した場合、自動的にロールバックされます
            - flush後、バッファは空になります
            - 通常、コンテキストマネージャー終了時に自動的に呼ばれます
        """
        # バッファが空の場合は何もしない
        if not self.items:
            return

        try:
            # bulk_save_objects()で一括挿入
            # 通常のadd()とcommit()の繰り返しより遥かに高速
            self.db.bulk_save_objects(self.items)

            # トランザクションをコミット
            self.db.commit()

            logger.info(f"Flushed {len(self.items)} items to database")

            # バッファをクリア（次のバッチのため）
            self.items = []
        except Exception as e:
            # エラー時はロールバック
            self.db.rollback()

            # エラーを適切な例外に変換して再送出
            handle_database_error(e)

    def __enter__(self):
        """
        コンテキストマネージャーのenter処理

        withステートメントでBatchProcessorを使用できるようにします。

        Returns:
            BatchProcessor: 自身のインスタンス

        Examples:
            >>> with BatchProcessor(db) as processor:
            ...     processor.add(User(username="alice"))
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        コンテキストマネージャーのexit処理

        withブロックを抜ける際に、バッファに残っているアイテムを
        自動的にflush()します。これにより、最後のバッチが確実に保存されます。

        Args:
            exc_type: 例外のタイプ（例外がない場合None）
            exc_val: 例外の値（例外がない場合None）
            exc_tb: トレースバック（例外がない場合None）

        Examples:
            >>> with BatchProcessor(db, batch_size=100) as processor:
            ...     for i in range(150):
            ...         processor.add(User(username=f"user_{i}"))
            ...     # 100件は自動flushされ、残り50件はここで自動flush
        """
        # 残りのアイテムをflush
        self.flush()


def paginate_query(query, limit: int, offset: int):
    """
    クエリにページネーションを適用します

    大量のデータを取得する際に、一度に全件取得するのではなく、
    ページ単位で分割して取得するための関数です。
    APIのレスポンス時間を短縮し、メモリ使用量を削減します。

    ページネーションの仕組み:
        - limit: 1ページあたりの件数
        - offset: 開始位置（スキップする件数）
        - ページ番号からoffsetを計算: offset = (page - 1) * limit

    例: limit=10, offset=20 の場合
        - 21番目から30番目のレコードを取得
        - これは3ページ目に相当（1ページ10件の場合）

    Args:
        query: SQLAlchemyのクエリオブジェクト。
              例: db.query(User).filter(User.is_active == True)
        limit (int): 取得する最大件数（ページサイズ）。
                    通常は10、20、50、100などの値を使用。
        offset (int): スキップする件数（開始位置）。
                     0から開始（0 = 最初のレコードから）。

    Returns:
        Query: limit()とoffset()が適用されたSQLAlchemyクエリオブジェクト。
              all()やfirst()で実行可能。

    Examples:
        >>> # 基本的な使用（1ページ目、20件ずつ）
        >>> query = db.query(User)
        >>> paginated_query = paginate_query(query, limit=20, offset=0)
        >>> users = paginated_query.all()

        >>> # 2ページ目を取得
        >>> page = 2
        >>> limit = 20
        >>> offset = (page - 1) * limit  # offset = 20
        >>> query = db.query(User).order_by(User.created_at.desc())
        >>> users = paginate_query(query, limit, offset).all()

        >>> # エンドポイントでの使用
        >>> @router.get("/users")
        >>> async def list_users(
        ...     page: int = 1,
        ...     page_size: int = 20,
        ...     db: Session = Depends(get_db)
        ... ):
        ...     offset = (page - 1) * page_size
        ...     query = db.query(User).filter(User.is_active == True)
        ...     users = paginate_query(query, page_size, offset).all()
        ...     total = query.count()  # ページネーション前のカウント
        ...     return {
        ...         "items": users,
        ...         "total": total,
        ...         "page": page,
        ...         "page_size": page_size
        ...     }

    Note:
        - offsetを使用したページネーションは大きなoffset値でパフォーマンスが低下します
        - 非常に大量のデータの場合、カーソルベースのページネーションを検討してください
        - order_by()を必ず指定してください（結果の順序を保証するため）
        - count()は別途実行する必要があります（全件数を知るため）

    ベストプラクティス:
        - limitの最大値を制限（例: 100件まで）して過負荷を防ぐ
        - デフォルト値を設定（例: limit=20, page=1）
        - 必ずorder_by()と組み合わせて使用
        - 総ページ数を計算してクライアントに返す

    パフォーマンスの考慮:
        - offset値が大きい場合（例: offset=10000）、データベースは
          最初の10000件を内部的にスキャンする必要があります
        - 代替案: created_at > last_seen_timestamp のような条件でフィルタリング
    """
    return query.limit(limit).offset(offset)
