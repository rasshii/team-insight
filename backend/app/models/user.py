from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.db.base_class import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = {"schema": "team_insight"}

    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Email verification fields
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String, nullable=True)
    email_verification_token_expires = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    backlog_id = Column(Integer, unique=True, index=True, nullable=True)
    user_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)

    oauth_tokens = relationship(
        "OAuthToken", back_populates="user", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", secondary="team_insight.project_members", back_populates="members"
    )

    @property
    def roles(self):
        """ユーザーのロール一覧を取得（UserRoleを介して）"""
        return self.user_roles

    _is_admin_cached = None  # 管理者権限のキャッシュ

    @hybrid_property
    def is_admin(self):
        """
        管理者権限を持っているかチェック（N+1問題対策済み）
        
        管理者権限の判定ロジック:
        1. is_superuserがTrueの場合は管理者
        2. グローバルなADMINロールを持つ場合は管理者
        
        注意: user_rolesとroleがeager loadingされている前提で動作します。
        適切にjoinedload()を使用してクエリしてください。
        """
        # キャッシュが存在する場合はそれを返す
        if self._is_admin_cached is not None:
            return self._is_admin_cached
            
        if self.is_superuser:
            self._is_admin_cached = True
            return True
        
        # user_rolesがロードされていない場合はFalseを返す（N+1防止）
        if not hasattr(self, '_sa_instance_state') or 'user_roles' not in self.__dict__:
            return False
            
        # ロールのチェック（eager loadingされている前提）
        self._is_admin_cached = any(
            ur.role.name == "ADMIN"
            for ur in self.user_roles
            if ur.project_id is None  # グローバルロールのみチェック
        )
        return self._is_admin_cached
    
    @is_admin.expression
    def is_admin(cls):
        """SQLクエリレベルでの管理者判定（クエリ最適化用）"""
        from sqlalchemy import exists, and_
        from app.models.rbac import UserRole, Role
        
        return cls.is_superuser | exists().where(
            and_(
                UserRole.user_id == cls.id,
                UserRole.project_id.is_(None),
                UserRole.role_id == Role.id,
                Role.name == "ADMIN"
            )
        )
    
    # タスク関連のリレーション
    assigned_tasks = relationship(
        "Task", foreign_keys="Task.assignee_id", back_populates="assignee"
    )
    reported_tasks = relationship(
        "Task", foreign_keys="Task.reporter_id", back_populates="reporter"
    )
    
    # 同期履歴のリレーション
    sync_histories = relationship(
        "SyncHistory", back_populates="user", cascade="all, delete-orphan"
    )
