# backend/app/core/permissions.py

from enum import Enum
from typing import List, Optional
from functools import wraps
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.rbac import UserRole, Role
from app.models.project import Project

class RoleType(str, Enum):
    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    MEMBER = "MEMBER"

class PermissionChecker:
    """
    権限チェックを行うクラス

    設計のポイント：
    1. 階層的な権限（上位ロールは下位ロールの権限を含む）
    2. プロジェクト単位の権限管理
    3. デコレータパターンで使いやすく
    """

    @staticmethod
    def has_role(user: User, role: RoleType, project_id: Optional[int] = None) -> bool:
        """ユーザーが指定されたロールを持っているかチェック"""
        # 管理者は全権限を持つ
        if user.is_admin:
            return True

        user_roles = user.roles

        # プロジェクト指定がある場合
        if project_id:
            project_roles = [r for r in user_roles if r.project_id == project_id]
            return any(r.role.name == role.value for r in project_roles)

        # グローバルロールのチェック
        global_roles = [r for r in user_roles if r.project_id is None]
        return any(r.role.name == role.value for r in global_roles)

    @staticmethod
    def check_project_access(user: User, project_id: int, db: Session) -> bool:
        """
        プロジェクトへのアクセス権限をチェック
        
        注意: project_idに対応するProjectは、呼び出し元でeager loadingされていることを想定
        """
        # 管理者は全プロジェクトにアクセス可能
        if user.is_admin:
            return True

        # プロジェクトメンバーかチェック
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
            
        return user in project.members
    
    @staticmethod
    def check_project_permission(
        user: User, 
        project_id: int, 
        required_role: RoleType,
        db: Session
    ) -> bool:
        """プロジェクト内での特定の権限をチェック"""
        # 管理者は全権限を持つ
        if user.is_admin:
            return True
            
        # プロジェクトへのアクセス権限を確認
        if not PermissionChecker.check_project_access(user, project_id, db):
            return False
            
        # プロジェクト内での役割を確認
        return PermissionChecker.has_role(user, required_role, project_id)

def require_role(roles: List[RoleType]):
    """
    ロールベースのアクセス制御デコレータ

    使用例:
    @router.get("/admin/users")
    @require_role([RoleType.ADMIN])
    async def get_users():
        ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 現在のユーザーを取得
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="認証が必要です"
                )

            # 権限チェック
            has_permission = False
            for role in roles:
                if PermissionChecker.has_role(current_user, role):
                    has_permission = True
                    break

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="この操作を実行する権限がありません"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
