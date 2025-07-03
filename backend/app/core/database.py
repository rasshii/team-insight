"""
データベース関連のユーティリティ
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
    
    使用例:
        with transaction(db) as session:
            # データベース操作
            user = User(...)
            session.add(user)
            # withブロックを抜けると自動的にcommit
            # エラーが発生した場合は自動的にrollback
    
    Args:
        db: SQLAlchemyセッション
        
    Yields:
        トランザクション内で使用するセッション
    """
    try:
        logger.debug("Starting database transaction")
        yield db
        db.commit()
        logger.debug("Database transaction committed")
    except Exception as e:
        logger.error(f"Database transaction failed: {str(e)}")
        db.rollback()
        handle_database_error(e)
    finally:
        db.close()


class BatchProcessor:
    """
    バッチ処理用ユーティリティ
    """
    
    def __init__(self, db: Session, batch_size: int = 100):
        self.db = db
        self.batch_size = batch_size
        self.items = []
    
    def add(self, item):
        """アイテムをバッチに追加"""
        self.items.append(item)
        if len(self.items) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """バッチをデータベースにフラッシュ"""
        if not self.items:
            return
        
        try:
            self.db.bulk_save_objects(self.items)
            self.db.commit()
            logger.info(f"Flushed {len(self.items)} items to database")
            self.items = []
        except Exception as e:
            self.db.rollback()
            handle_database_error(e)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()


def paginate_query(query, limit: int, offset: int):
    """
    クエリにページネーションを適用
    
    Args:
        query: SQLAlchemyクエリ
        limit: 取得件数
        offset: オフセット
        
    Returns:
        ページネーションが適用されたクエリ
    """
    return query.limit(limit).offset(offset)
