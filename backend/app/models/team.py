"""
チーム管理モデル

Team Insight独自のチーム概念を管理するモデル。
Backlogのプロジェクトとは独立して、組織内のチームを定義。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base_class import Base


class TeamRole(str, enum.Enum):
    """チーム内での役割"""
    TEAM_LEADER = "team_leader"
    MEMBER = "member"


class Team(Base):
    """
    チームモデル
    
    Team Insight内で独自に定義されるチーム。
    複数のユーザーが所属し、生産性分析の単位となる。
    """
    __tablename__ = "teams"
    __table_args__ = {'schema': 'team_insight'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name={self.name})>"


class TeamMember(Base):
    """
    チームメンバー中間テーブル
    
    ユーザーとチームの多対多関係を管理し、
    チーム内での役割も保持する。
    """
    __tablename__ = "team_members"
    __table_args__ = {'schema': 'team_insight'}

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("team_insight.teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("team_insight.users.id"), nullable=False)
    role = Column(String(50), nullable=False, default=TeamRole.MEMBER)
    
    # タイムスタンプ
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # リレーション
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")
    
    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"