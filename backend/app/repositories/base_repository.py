"""
リポジトリ基底クラス - データアクセス層の抽象化

このモジュールは、すべてのリポジトリクラスの基底となる汎用的なCRUD操作を提供します。

主要機能：
1. 基本的なCRUD操作（Create, Read, Update, Delete）
2. ページネーション対応の複数レコード取得
3. フィルタリング機能
4. カウント機能
5. バルク操作のサポート

設計原則：
- 単一責任の原則（データアクセスのみ）
- 依存性注入（SessionとModelを外部から受け取る）
- ジェネリック型による型安全性
- SQLAlchemyのクエリ最適化

使用例：
    class UserRepository(BaseRepository[User]):
        def __init__(self, db: Session):
            super().__init__(User, db)

        def get_by_email(self, email: str) -> Optional[User]:
            return self.db.query(self.model).filter(
                self.model.email == email
            ).first()
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.base_class import Base

# ジェネリック型変数（任意のSQLAlchemyモデルを表現）
ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    リポジトリの基底クラス

    すべてのリポジトリクラスが継承する抽象的なデータアクセス層を提供します。
    ジェネリック型を使用することで、型安全性を保ちながら再利用可能なコードを実現。

    主要メソッド：
    - get: IDによる単一レコード取得
    - get_multi: 複数レコード取得（フィルタリング、ページネーション対応）
    - create: 新規レコード作成
    - update: 既存レコード更新
    - delete: レコード削除
    - count: レコード件数カウント
    - exists: レコード存在チェック

    パフォーマンス最適化：
    - 必要最小限のクエリ発行
    - インデックスを活用した効率的な検索
    - N+1問題の回避（外部でeager loadingを指定）

    Attributes:
        model (Type[ModelT]): 対象のSQLAlchemyモデルクラス
        db (Session): SQLAlchemyのデータベースセッション
    """

    def __init__(self, model: Type[ModelT], db: Session):
        """
        リポジトリの初期化

        Args:
            model (Type[ModelT]): 操作対象のSQLAlchemyモデルクラス
            db (Session): データベースセッション
        """
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelT]:
        """
        IDで単一レコードを取得

        プライマリキー（ID）を使用した最も効率的な取得方法です。
        インデックスが効くため、O(1)に近い高速な検索が可能です。

        Args:
            id (int): 取得するレコードのID

        Returns:
            Optional[ModelT]: 見つかった場合はモデルインスタンス、見つからない場合はNone

        Example:
            >>> user_repo = UserRepository(db)
            >>> user = user_repo.get(1)
            >>> if user:
            ...     print(user.name)

        Note:
            - リレーションを取得する場合は、呼び出し側でjoinedload()を使用
            - このメソッドはセッションにキャッシュされます
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelT]:
        """
        複数レコードを取得（フィルタリング、ソート、ページネーション対応）

        柔軟なフィルタリングとページネーションをサポートする汎用的な取得メソッド。
        大量データを扱う際のパフォーマンスを考慮し、limit/offsetによる
        効率的なページング機能を提供します。

        フィルタリング機能：
        - filtersパラメータで等価条件を指定可能
        - 複雑な条件は各リポジトリで専用メソッドを実装推奨

        ソート機能：
        - order_byでカラム名を指定
        - order_descでソート順を制御（True: 降順、False: 昇順）

        Args:
            skip (int, optional): スキップするレコード数（オフセット）。デフォルトは0
            limit (int, optional): 取得する最大レコード数。デフォルトは100
            filters (Optional[Dict[str, Any]], optional):
                フィルタ条件の辞書。キーはカラム名、値は検索値。
                例: {"status": "active", "is_deleted": False}
            order_by (Optional[str], optional):
                ソートするカラム名。デフォルトはNone（ソートなし）
            order_desc (bool, optional):
                降順ソートフラグ。Trueで降順、Falseで昇順。デフォルトはFalse

        Returns:
            List[ModelT]: 条件に一致するモデルインスタンスのリスト

        Example:
            >>> # 基本的な使用例
            >>> users = user_repo.get_multi(skip=0, limit=10)

            >>> # フィルタリングとソート
            >>> active_users = user_repo.get_multi(
            ...     filters={"is_active": True},
            ...     order_by="created_at",
            ...     order_desc=True,
            ...     limit=20
            ... )

        Note:
            - 大量データの場合、limitを適切に設定してメモリ使用量を制御
            - インデックスが張られたカラムでフィルタリング/ソートすると高速
            - N+1問題を避けるため、リレーション取得は呼び出し側でjoinedload()使用
        """
        # ベースクエリの構築
        query = self.db.query(self.model)

        # フィルタ条件の適用
        if filters:
            for key, value in filters.items():
                # モデルに属性が存在する場合のみフィルタを適用
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # ソート条件の適用
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        # ページネーションの適用と結果の取得
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelT:
        """
        新規レコードを作成

        辞書形式のデータからモデルインスタンスを生成し、データベースに永続化します。
        トランザクション管理は呼び出し側で行うことを推奨します。

        処理フロー：
        1. 辞書データからモデルインスタンスを生成
        2. セッションに追加
        3. データベースに即座に反映（flush）してIDを取得
        4. 最新のデータで更新（refresh）

        Args:
            obj_in (Dict[str, Any]):
                作成するレコードのデータ辞書。
                キーはモデルのカラム名、値はそのカラムの値。
                例: {"name": "John", "email": "john@example.com"}

        Returns:
            ModelT: 作成されたモデルインスタンス（IDが自動採番される）

        Example:
            >>> user_data = {"name": "Alice", "email": "alice@example.com"}
            >>> new_user = user_repo.create(user_data)
            >>> print(f"Created user with ID: {new_user.id}")

        Raises:
            IntegrityError: ユニーク制約違反などのDB制約エラー
            ValueError: 無効なカラム名や型の不一致

        Note:
            - このメソッドはdb.commit()を実行しません（呼び出し側で制御）
            - db.flush()により、IDなどの自動採番値が取得可能
            - バリデーションはService層で行うことを推奨
        """
        # 辞書データからモデルインスタンスを生成
        db_obj = self.model(**obj_in)

        # セッションに追加
        self.db.add(db_obj)

        # データベースに反映（IDの自動採番を取得）
        self.db.flush()

        # 最新の状態で更新（リレーションなどを含む）
        self.db.refresh(db_obj)

        return db_obj

    def update(self, db_obj: ModelT, obj_in: Dict[str, Any]) -> ModelT:
        """
        既存レコードを更新

        既存のモデルインスタンスに対して、辞書形式の更新データを適用します。
        指定されたフィールドのみを更新し、その他のフィールドは保持されます。

        更新処理の特徴：
        - 部分更新対応（指定したフィールドのみ更新）
        - 存在しないフィールドは無視（安全性向上）
        - updated_atなどのタイムスタンプは自動更新

        Args:
            db_obj (ModelT): 更新対象の既存モデルインスタンス
            obj_in (Dict[str, Any]):
                更新するフィールドと値の辞書。
                例: {"name": "Jane", "is_active": False}

        Returns:
            ModelT: 更新されたモデルインスタンス

        Example:
            >>> user = user_repo.get(1)
            >>> update_data = {"name": "Updated Name"}
            >>> updated_user = user_repo.update(user, update_data)
            >>> print(updated_user.name)  # "Updated Name"

        Note:
            - db_objは事前に取得済みのインスタンスである必要があります
            - db.commit()は呼び出し側で実行してください
            - リレーションの更新には別途専用メソッドの実装を推奨
        """
        # 更新データの各フィールドを既存オブジェクトに適用
        for key, value in obj_in.items():
            # モデルに属性が存在する場合のみ更新（安全性確保）
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        # データベースに変更を反映
        self.db.flush()

        # 最新の状態で更新
        self.db.refresh(db_obj)

        return db_obj

    def delete(self, id: int) -> bool:
        """
        レコードを削除

        指定されたIDのレコードを物理削除します。
        論理削除（ソフトデリート）が必要な場合は、各リポジトリで
        専用の論理削除メソッドを実装してください。

        削除処理の流れ：
        1. IDでレコードを検索
        2. 存在する場合は削除を実行
        3. 存在しない場合はFalseを返す

        Args:
            id (int): 削除するレコードのID

        Returns:
            bool: 削除成功時はTrue、レコードが存在しない場合はFalse

        Example:
            >>> if user_repo.delete(1):
            ...     print("User deleted successfully")
            ... else:
            ...     print("User not found")

        Note:
            - カスケード削除の動作はモデルのリレーション定義に依存
            - db.commit()は呼び出し側で実行してください
            - 重要なデータの場合は論理削除（is_deleted フラグ）を推奨
        """
        # レコードを取得
        obj = self.get(id)

        if obj:
            # 存在する場合は削除
            self.db.delete(obj)
            self.db.flush()
            return True

        # 存在しない場合は削除失敗
        return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        条件に一致するレコードの件数を取得

        フィルタ条件に一致するレコード数を効率的にカウントします。
        ページネーションの総件数表示などに使用されます。

        パフォーマンス最適化：
        - COUNT(*)クエリによる高速カウント
        - インデックスを活用した効率的な集計
        - 不要なデータのロードを回避

        Args:
            filters (Optional[Dict[str, Any]], optional):
                フィルタ条件の辞書。キーはカラム名、値は検索値。
                Noneの場合は全件をカウント。
                例: {"is_active": True}

        Returns:
            int: 条件に一致するレコードの件数

        Example:
            >>> # 全ユーザー数をカウント
            >>> total_users = user_repo.count()
            >>> print(f"Total users: {total_users}")

            >>> # アクティブなユーザーのみカウント
            >>> active_users = user_repo.count(filters={"is_active": True})
            >>> print(f"Active users: {active_users}")

        Note:
            - 大量データでもパフォーマンスが良好（インデックス利用時）
            - フィルタ条件はget_multiと同様の形式
        """
        # ベースクエリの構築
        query = self.db.query(func.count(self.model.id))

        # フィルタ条件の適用
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        # 件数を取得
        return query.scalar() or 0

    def exists(self, id: int) -> bool:
        """
        指定されたIDのレコードが存在するかチェック

        レコードの存在確認のみを行う軽量なメソッドです。
        EXISTS句を使用することで、不要なデータ取得を避け、
        パフォーマンスを最適化します。

        Args:
            id (int): 存在確認するレコードのID

        Returns:
            bool: レコードが存在する場合True、存在しない場合False

        Example:
            >>> if user_repo.exists(1):
            ...     print("User exists")
            ... else:
            ...     print("User not found")

        Note:
            - get()よりも軽量（データのロードが不要）
            - EXISTS句により効率的なクエリが発行される
        """
        return self.db.query(self.db.query(self.model).filter(self.model.id == id).exists()).scalar()

    def bulk_create(self, obj_list: List[Dict[str, Any]]) -> List[ModelT]:
        """
        複数レコードを一括作成

        複数のレコードを効率的に一括挿入します。
        個別にinsertするよりもパフォーマンスが大幅に向上します。

        バルク挿入の利点：
        - 1回のトランザクションで複数レコードを挿入
        - ネットワークラウンドトリップの削減
        - データベース負荷の軽減

        Args:
            obj_list (List[Dict[str, Any]]):
                作成するレコードのデータ辞書のリスト
                例: [{"name": "Alice"}, {"name": "Bob"}]

        Returns:
            List[ModelT]: 作成されたモデルインスタンスのリスト

        Example:
            >>> users_data = [
            ...     {"name": "Alice", "email": "alice@example.com"},
            ...     {"name": "Bob", "email": "bob@example.com"}
            ... ]
            >>> new_users = user_repo.bulk_create(users_data)
            >>> print(f"Created {len(new_users)} users")

        Note:
            - 大量データの場合は、チャンクに分割して実行を推奨
            - トリガーやデフォルト値の処理に注意
            - db.commit()は呼び出し側で実行
        """
        # 辞書データからモデルインスタンスのリストを生成
        db_objs = [self.model(**obj_data) for obj_data in obj_list]

        # 一括追加
        self.db.bulk_save_objects(db_objs)
        self.db.flush()

        return db_objs
