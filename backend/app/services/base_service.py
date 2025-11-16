"""
サービス層の基底クラス

このモジュールは、すべてのサービスクラスが継承する基底クラスと
共通的なサービス機能を提供します。
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel
from datetime import datetime, timezone
import logging
from abc import ABC, abstractmethod

from app.db.base_class import Base
from app.core.exceptions import NotFoundException, DatabaseException, PermissionDenied
from app.core.permissions import PermissionChecker
from app.models.user import User

# 型変数
ModelT = TypeVar("ModelT", bound=Base)
SchemaT = TypeVar("SchemaT", bound=BaseModel)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseService(ABC, Generic[ModelT, SchemaT, CreateSchemaT, UpdateSchemaT]):
    """
    CRUDサービスの基底クラス

    すべてのサービスクラスが継承し、共通のCRUD操作を提供します。
    """

    def __init__(self, model: Type[ModelT]):
        """
        Args:
            model: SQLAlchemyモデルクラス
        """
        self.model = model
        self.logger = logging.getLogger(f"{__name__}.{model.__name__}Service")

    @abstractmethod
    def get_base_query(self, db: Session) -> Query:
        """
        基本クエリを取得（サブクラスでオーバーライド可能）

        Args:
            db: データベースセッション

        Returns:
            基本クエリオブジェクト
        """
        return db.query(self.model)

    def get(self, db: Session, id: int) -> Optional[ModelT]:
        """
        IDでエンティティを取得

        Args:
            db: データベースセッション
            id: エンティティID

        Returns:
            エンティティまたはNone
        """
        try:
            return self.get_base_query(db).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting {self.model.__name__} with id {id}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の取得に失敗しました")

    def get_or_404(self, db: Session, id: int) -> ModelT:
        """
        IDでエンティティを取得（存在しない場合は例外）

        Args:
            db: データベースセッション
            id: エンティティID

        Returns:
            エンティティ

        Raises:
            NotFoundException: エンティティが見つからない場合
        """
        obj = self.get(db, id)
        if not obj:
            raise NotFoundException(resource=self.model.__name__, identifier=id)
        return obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[ModelT]:
        """
        複数のエンティティを取得

        Args:
            db: データベースセッション
            skip: スキップ件数
            limit: 取得件数
            filters: フィルター条件
            order_by: ソート条件

        Returns:
            エンティティのリスト
        """
        try:
            query = self.get_base_query(db)

            # フィルター適用
            if filters:
                query = self._apply_filters(query, filters)

            # ソート適用
            if order_by:
                query = self._apply_order_by(query, order_by)

            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting multiple {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}一覧の取得に失敗しました")

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        エンティティ数を取得

        Args:
            db: データベースセッション
            filters: フィルター条件

        Returns:
            エンティティ数
        """
        try:
            query = self.get_base_query(db)

            if filters:
                query = self._apply_filters(query, filters)

            return query.count()
        except SQLAlchemyError as e:
            self.logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}のカウントに失敗しました")

    def create(self, db: Session, *, obj_in: CreateSchemaT) -> ModelT:
        """
        エンティティを作成

        Args:
            db: データベースセッション
            obj_in: 作成データ

        Returns:
            作成されたエンティティ
        """
        try:
            db_obj = self.model(**obj_in.dict())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error creating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の作成に失敗しました（制約違反）")
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の作成に失敗しました")

    def update(self, db: Session, *, db_obj: ModelT, obj_in: Union[UpdateSchemaT, Dict[str, Any]]) -> ModelT:
        """
        エンティティを更新

        Args:
            db: データベースセッション
            db_obj: 更新対象のエンティティ
            obj_in: 更新データ

        Returns:
            更新されたエンティティ
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            # 更新日時を設定
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.now(timezone.utc)

            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error updating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の更新に失敗しました（制約違反）")
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の更新に失敗しました")

    def delete(self, db: Session, *, id: int) -> ModelT:
        """
        エンティティを削除

        Args:
            db: データベースセッション
            id: エンティティID

        Returns:
            削除されたエンティティ
        """
        try:
            obj = self.get_or_404(db, id)
            db.delete(obj)
            db.commit()
            return obj
        except NotFoundException:
            raise
        except IntegrityError as e:
            db.rollback()
            self.logger.error(f"Integrity error deleting {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の削除に失敗しました（制約違反）")
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise DatabaseException(f"{self.model.__name__}の削除に失敗しました")

    def exists(self, db: Session, *, id: int) -> bool:
        """
        エンティティの存在確認

        Args:
            db: データベースセッション
            id: エンティティID

        Returns:
            存在する場合True
        """
        try:
            return self.get_base_query(db).filter(self.model.id == id).exists().scalar()
        except SQLAlchemyError as e:
            self.logger.error(f"Error checking existence of {self.model.__name__}: {str(e)}")
            return False

    def _apply_filters(self, query: Query, filters: Dict[str, Any]) -> Query:
        """
        クエリにフィルターを適用

        Args:
            query: クエリオブジェクト
            filters: フィルター条件

        Returns:
            フィルター適用後のクエリ
        """
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query

    def _apply_order_by(self, query: Query, order_by: str) -> Query:
        """
        クエリにソートを適用

        Args:
            query: クエリオブジェクト
            order_by: ソート条件（例: "created_at desc"）

        Returns:
            ソート適用後のクエリ
        """
        parts = order_by.split()
        if len(parts) == 1:
            field = parts[0]
            desc = False
        else:
            field = parts[0]
            desc = parts[1].lower() == "desc"

        if hasattr(self.model, field):
            column = getattr(self.model, field)
            if desc:
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column)

        return query


class SecureService(BaseService[ModelT, SchemaT, CreateSchemaT, UpdateSchemaT]):
    """
    セキュアなサービスの基底クラス

    権限チェックを含むCRUD操作を提供します。
    """

    @abstractmethod
    def check_read_permission(self, db: Session, user: User, obj: ModelT) -> bool:
        """
        読み取り権限をチェック

        Args:
            db: データベースセッション
            user: 現在のユーザー
            obj: 対象オブジェクト

        Returns:
            権限がある場合True
        """
        pass

    @abstractmethod
    def check_write_permission(self, db: Session, user: User, obj: Optional[ModelT] = None) -> bool:
        """
        書き込み権限をチェック

        Args:
            db: データベースセッション
            user: 現在のユーザー
            obj: 対象オブジェクト（作成時はNone）

        Returns:
            権限がある場合True
        """
        pass

    def get_secure(self, db: Session, id: int, user: User) -> Optional[ModelT]:
        """
        権限チェック付きでエンティティを取得

        Args:
            db: データベースセッション
            id: エンティティID
            user: 現在のユーザー

        Returns:
            エンティティまたはNone

        Raises:
            PermissionDenied: 権限がない場合
        """
        obj = self.get(db, id)
        if obj and not self.check_read_permission(db, user, obj):
            return None
        return obj

    def create_secure(self, db: Session, *, obj_in: CreateSchemaT, user: User) -> ModelT:
        """
        権限チェック付きでエンティティを作成

        Args:
            db: データベースセッション
            obj_in: 作成データ
            user: 現在のユーザー

        Returns:
            作成されたエンティティ

        Raises:
            PermissionDenied: 権限がない場合
        """
        if not self.check_write_permission(db, user):
            raise PermissionDenied("作成権限がありません")
        return self.create(db, obj_in=obj_in)
