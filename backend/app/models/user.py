from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}

    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    backlog_id = Column(Integer, unique=True, index=True, nullable=True)
    user_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)

    oauth_tokens = relationship(
        "OAuthToken", back_populates="user", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def roles(self):
        """ユーザーのロール一覧を取得（UserRoleを介して）"""
        return self.user_roles

    @property
    def is_admin(self):
        """
        管理者権限を持っているかチェック
        
        管理者権限の判定ロジック:
        1. is_superuserがTrueの場合は管理者
        2. グローバルなADMINロールを持つ場合は管理者
        """
        if self.is_superuser:
            return True
            
        # N+1問題を防ぐため、user_rolesが読み込まれている前提で動作
        # 必要に応じてjoinedloadやselectinloadを使用すること
        return any(
            ur.role.name == "ADMIN"
            for ur in self.user_roles
            if ur.project_id is None  # グローバルロールのみチェック
        )

    projects = relationship(
        "Project", secondary="team_insight.project_members", back_populates="members"
    )
    
    # タスク関連のリレーション
    assigned_tasks = relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee"
    )
    reported_tasks = relationship(
        "Task", foreign_keys="Task.reporter_id", back_populates="reporter"
    )
