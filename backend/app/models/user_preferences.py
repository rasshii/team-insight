"""
ユーザー設定関連のSQLAlchemyモデル
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class UserPreferences(Base):
    """ユーザー通知設定"""

    __tablename__ = "user_preferences"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), unique=True, nullable=False)

    # 通知設定
    email_notifications = Column(Boolean, default=True)
    report_frequency = Column(String(20), default="weekly")  # daily, weekly, monthly
    notification_email = Column(String(255))

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # リレーション
    user = relationship("User", back_populates="preferences")


class LoginHistory(Base):
    """ログイン履歴"""

    __tablename__ = "login_history"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)

    # ログイン情報
    ip_address = Column(String(45))
    user_agent = Column(Text)
    login_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    logout_at = Column(DateTime(timezone=True))
    session_id = Column(String(255))

    # リレーション
    user = relationship("User", back_populates="login_history")


class ActivityLog(Base):
    """アクティビティログ"""

    __tablename__ = "activity_logs"
    __table_args__ = {"schema": "team_insight"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)

    # アクティビティ情報
    action = Column(String(100), nullable=False)  # login, logout, update_profile, etc.
    resource_type = Column(String(50))  # user, project, team, etc.
    resource_id = Column(Integer)
    details = Column(JSON)  # 追加情報
    ip_address = Column(String(45))

    # タイムスタンプ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # リレーション
    user = relationship("User", back_populates="activity_logs")
