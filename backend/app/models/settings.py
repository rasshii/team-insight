"""
設定管理のSQLAlchemyモデル
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base


class SystemSetting(Base):
    """
    システム設定モデル

    key-value形式で設定を保存し、設定のグループ化と型情報を持つ
    """

    __tablename__ = "system_settings"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    group = Column(String(100), nullable=False, index=True)  # email, security, sync, system
    value_type = Column(String(50), nullable=False, default="string")  # string, integer, boolean, json
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # パスワードなど機密情報フラグ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', group='{self.group}')>"
