"""
認証関連のデータベースモデル

このモジュールは、OAuth2.0トークンやユーザー認証情報を
保存するためのデータベースモデルを定義します。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base
from app.models.user import User


class OAuthToken(Base):
    """
    OAuthトークンを保存するモデル

    各ユーザーのOAuth2.0アクセストークンとリフレッシュトークンを
    プロバイダー（Backlogなど）ごとに保存します。
    """
    __tablename__ = "oauth_tokens"
    __table_args__ = {'schema': 'team_insight'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    provider = Column(String(50), nullable=False)  # "backlog"など
    access_token = Column(Text, nullable=False)  # アクセストークン
    refresh_token = Column(Text, nullable=True)  # リフレッシュトークン
    expires_at = Column(DateTime, nullable=True)  # トークンの有効期限
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    user = relationship("User", back_populates="oauth_tokens")

    def is_expired(self) -> bool:
        """
        トークンが期限切れかどうかを確認

        Returns:
            期限切れの場合True、そうでない場合False
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<OAuthToken(user_id={self.user_id}, provider={self.provider})>"


class OAuthState(Base):
    """
    OAuth認証フローのstateパラメータを一時的に保存するモデル

    CSRF攻撃を防ぐため、認証フロー開始時に生成したstateを
    一時的に保存し、コールバック時に検証します。
    """
    __tablename__ = "oauth_states"
    __table_args__ = {'schema': 'team_insight'}

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=True)  # ログイン済みユーザーの場合
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # 有効期限（通常10分程度）

    def is_expired(self) -> bool:
        """
        stateが期限切れかどうかを確認

        Returns:
            期限切れの場合True、そうでない場合False
        """
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<OAuthState(state={self.state[:10]}...)>"
