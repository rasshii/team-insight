"""
データベースモデルのベースクラス

すべてのSQLAlchemyモデルが継承する基底クラスを定義します。
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from zoneinfo import ZoneInfo

# SQLAlchemyのベースクラス
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now(ZoneInfo("Asia/Tokyo")))
    updated_at = Column(DateTime, default=datetime.now(ZoneInfo("Asia/Tokyo"),), onupdate=datetime.now(ZoneInfo("Asia/Tokyo")))
