"""
データベースモデルのベースクラス

すべてのSQLAlchemyモデルが継承する基底クラスを定義します。
"""

from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemyのベースクラス
Base = declarative_base()
