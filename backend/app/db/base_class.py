"""
データベースモデルのベースクラス

すべてのSQLAlchemyモデルが継承する基底クラスを定義します。
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from app.core.datetime_utils import utcnow

# SQLAlchemyのベースクラス
Base = declarative_base()


class BaseModel(Base):
    """すべてのモデルの基底クラス

    - データベースにはUTCタイムゾーン付きで保存
    - APIレスポンスではJSTに変換して返却
    """

    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
