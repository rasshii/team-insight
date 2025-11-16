"""
クエリ最適化ユーティリティ

このモジュールは、SQLAlchemyクエリの最適化とN+1問題の解決を
支援するユーティリティを提供します。
"""

from typing import List, Dict, Any, Optional, Type, Callable
from sqlalchemy.orm import Query, Session, joinedload, selectinload, subqueryload, contains_eager
from sqlalchemy.sql import and_, or_
from sqlalchemy import func
from functools import wraps
import logging

from app.db.base_class import Base

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """クエリ最適化のためのヘルパークラス"""

    @staticmethod
    def with_joined(query: Query, *relationships: str) -> Query:
        """
        指定したリレーションシップをJOINで取得

        Args:
            query: ベースクエリ
            relationships: リレーションシップ名のリスト

        Returns:
            最適化されたクエリ
        """
        for relationship in relationships:
            if "." in relationship:
                # ネストしたリレーションシップの処理
                parts = relationship.split(".")
                query = query.options(joinedload(parts[0]).joinedload(".".join(parts[1:])))
            else:
                query = query.options(joinedload(relationship))
        return query

    @staticmethod
    def with_subquery(query: Query, *relationships: str) -> Query:
        """
        指定したリレーションシップをサブクエリで取得

        Args:
            query: ベースクエリ
            relationships: リレーションシップ名のリスト

        Returns:
            最適化されたクエリ
        """
        for relationship in relationships:
            if "." in relationship:
                parts = relationship.split(".")
                query = query.options(subqueryload(parts[0]).subqueryload(".".join(parts[1:])))
            else:
                query = query.options(subqueryload(relationship))
        return query

    @staticmethod
    def with_selectin(query: Query, *relationships: str) -> Query:
        """
        指定したリレーションシップをSELECT INで取得

        Args:
            query: ベースクエリ
            relationships: リレーションシップ名のリスト

        Returns:
            最適化されたクエリ
        """
        for relationship in relationships:
            if "." in relationship:
                parts = relationship.split(".")
                query = query.options(selectinload(parts[0]).selectinload(".".join(parts[1:])))
            else:
                query = query.options(selectinload(relationship))
        return query

    @staticmethod
    def paginate(query: Query, page: int = 1, per_page: int = 20, max_per_page: int = 100) -> tuple[List[Any], Dict[str, Any]]:
        """
        クエリをページネーション

        Args:
            query: ベースクエリ
            page: ページ番号（1始まり）
            per_page: 1ページあたりの件数
            max_per_page: 最大件数

        Returns:
            (結果リスト, ページネーション情報)
        """
        # per_pageの制限
        per_page = min(per_page, max_per_page)

        # 総件数を取得（最適化: COUNTクエリは別途実行）
        total = query.count()

        # ページ数計算
        total_pages = (total + per_page - 1) // per_page

        # 現在のページの結果を取得
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        # ページネーション情報
        pagination_info = {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }

        return items, pagination_info

    @staticmethod
    def bulk_load_relationships(db: Session, objects: List[Base], *relationships: str) -> None:
        """
        既存のオブジェクトに対してリレーションシップを一括ロード

        Args:
            db: データベースセッション
            objects: オブジェクトのリスト
            relationships: ロードするリレーションシップ
        """
        if not objects:
            return

        # オブジェクトのIDを収集
        ids = [obj.id for obj in objects]
        model = type(objects[0])

        # リレーションシップを含むクエリを実行
        query = db.query(model).filter(model.id.in_(ids))
        query = QueryOptimizer.with_selectin(query, *relationships)

        # 結果を取得（これによりリレーションシップがロードされる）
        query.all()


class CachedQuery:
    """キャッシュ付きクエリの実装"""

    def __init__(self, cache_key_prefix: str, ttl: int = 300):
        """
        Args:
            cache_key_prefix: キャッシュキーのプレフィックス
            ttl: キャッシュの有効期限（秒）
        """
        self.cache_key_prefix = cache_key_prefix
        self.ttl = ttl

    def get_or_execute(self, query: Query, cache_key_suffix: str = "", force_refresh: bool = False) -> List[Any]:
        """
        キャッシュから取得するか、クエリを実行

        Args:
            query: 実行するクエリ
            cache_key_suffix: キャッシュキーのサフィックス
            force_refresh: キャッシュを無視して実行

        Returns:
            クエリ結果
        """
        # TODO: Redisキャッシュの実装
        # 現在は単純にクエリを実行
        return query.all()


def optimize_query(load_relationships: Optional[List[str]] = None, use_cache: bool = False, cache_ttl: int = 300):
    """
    クエリ最適化デコレータ

    Args:
        load_relationships: 自動的にロードするリレーションシップ
        use_cache: キャッシュを使用するか
        cache_ttl: キャッシュの有効期限
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 関数を実行してクエリを取得
            result = func(*args, **kwargs)

            # Queryオブジェクトの場合、最適化を適用
            if isinstance(result, Query):
                if load_relationships:
                    result = QueryOptimizer.with_selectin(result, *load_relationships)

                # TODO: キャッシュの実装

            return result

        return wrapper

    return decorator


class QueryBuilder:
    """高度なクエリビルダー"""

    def __init__(self, base_query: Query):
        self.query = base_query
        self._joins = set()

    def filter_by_date_range(
        self, field: Any, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> "QueryBuilder":
        """
        日付範囲でフィルター

        Args:
            field: 日付フィールド
            start_date: 開始日
            end_date: 終了日

        Returns:
            self
        """
        conditions = []
        if start_date:
            conditions.append(field >= start_date)
        if end_date:
            conditions.append(field <= end_date)

        if conditions:
            self.query = self.query.filter(and_(*conditions))

        return self

    def search(self, search_term: str, *fields: Any, case_sensitive: bool = False) -> "QueryBuilder":
        """
        複数フィールドで検索

        Args:
            search_term: 検索語
            fields: 検索対象フィールド
            case_sensitive: 大文字小文字を区別するか

        Returns:
            self
        """
        if not search_term or not fields:
            return self

        conditions = []
        for field in fields:
            if case_sensitive:
                conditions.append(field.contains(search_term))
            else:
                conditions.append(func.lower(field).contains(search_term.lower()))

        self.query = self.query.filter(or_(*conditions))
        return self

    def order_by_multiple(self, *order_specs: tuple) -> "QueryBuilder":
        """
        複数条件でソート

        Args:
            order_specs: (フィールド, 'asc'|'desc')のタプル

        Returns:
            self
        """
        for field, direction in order_specs:
            if direction.lower() == "desc":
                self.query = self.query.order_by(field.desc())
            else:
                self.query = self.query.order_by(field.asc())

        return self

    def with_stats(self, group_by_field: Any) -> Query:
        """
        統計情報を含むクエリを生成

        Args:
            group_by_field: グループ化フィールド

        Returns:
            統計クエリ
        """
        return self.query.group_by(group_by_field).with_entities(
            group_by_field,
            func.count().label("count"),
            func.min(group_by_field).label("min"),
            func.max(group_by_field).label("max"),
        )

    def build(self) -> Query:
        """最終的なクエリを取得"""
        return self.query
