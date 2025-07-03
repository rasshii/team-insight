from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from app.db.base_class import BaseModel

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', Integer, ForeignKey('team_insight.roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('team_insight.permissions.id'), primary_key=True),
    schema='team_insight'
)

class Role(BaseModel):
    """
    ロールモデル
    
    システム内の役割を定義します。
    例: ADMIN, PROJECT_LEADER, MEMBER
    """
    __tablename__ = "roles"
    __table_args__ = {'schema': 'team_insight'}

    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    is_system = Column(Boolean, default=False)  # システムロール（削除不可）
    
    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

class Permission(BaseModel):
    """
    パーミッションモデル
    
    システム内の権限を定義します。
    例: users.read, users.write, projects.manage
    """
    __tablename__ = "permissions"
    __table_args__ = {'schema': 'team_insight'}

    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(50), nullable=False)  # リソース名（例: users, projects）
    action = Column(String(50), nullable=False)    # アクション名（例: read, write, delete）
    description = Column(String(255))
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserRole(BaseModel):
    """
    ユーザーロール関連モデル
    
    ユーザーとロールの関連を管理します。
    プロジェクト単位でのロール割り当てもサポートします。
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'project_id', name='_user_role_project_uc'),
        {'schema': 'team_insight'}
    )

    user_id = Column(Integer, ForeignKey('team_insight.users.id'), nullable=False)
    role_id = Column(Integer, ForeignKey('team_insight.roles.id'), nullable=False)
    project_id = Column(Integer, nullable=True)  # NULL = グローバルロール
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")