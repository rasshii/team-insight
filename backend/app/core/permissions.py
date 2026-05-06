"""
権限管理とアクセス制御 (Phase 0: organization_members.role + users.is_system_admin ベース)

旧 RBAC (user_roles / roles / role_permissions / permissions テーブル) を廃止し、
権限判定を以下の二本柱に集約した:
- users.is_system_admin: System Admin (テナントバイパス)
- organization_members.role: 組織内ロール (ADMIN / PROJECT_LEADER / MEMBER)

主要な API:
- RoleType: 組織内ロールの列挙型 (OrganizationRole と等価、互換エイリアス)
- PermissionChecker: 権限チェック静的メソッド群
- require_role: TenantContext ベースのロール必須デコレータ

ロール階層:
    ADMIN > PROJECT_LEADER > MEMBER (上位ロールは下位ロールの権限を内包)
"""

from enum import Enum
from functools import wraps
from typing import List, Optional

from fastapi import HTTPException, status

from app.core.tenant import TenantContext
from app.models.organization_member import OrganizationRole
from app.models.project import Project
from app.models.user import User


class RoleType(str, Enum):
    """
    ユーザーロール (OrganizationRole と等価、互換エイリアス)

    Phase 0 以前のコードからの互換性のため RoleType の名前を維持しているが、
    新規実装では OrganizationRole を直接使うことを推奨。
    """

    ADMIN = "ADMIN"
    PROJECT_LEADER = "PROJECT_LEADER"
    MEMBER = "MEMBER"

    def to_org_role(self) -> OrganizationRole:
        return OrganizationRole(self.value)


_ROLE_HIERARCHY = {
    RoleType.ADMIN.value: 3,
    RoleType.PROJECT_LEADER.value: 2,
    RoleType.MEMBER.value: 1,
}


def _role_satisfies(actual: str, required: RoleType) -> bool:
    """actual が required 以上の階層を満たすか"""
    return _ROLE_HIERARCHY.get(actual, 0) >= _ROLE_HIERARCHY[required.value]


class PermissionChecker:
    """
    権限チェック (静的メソッド群)

    Phase 0 で組織コンテキストベースに変更:
    - has_role: 指定組織での階層ロール判定
    - check_project_access: プロジェクトへのアクセス可否
    - check_project_permission: プロジェクト内ロール権限
    """

    @staticmethod
    def has_role(user: User, role: RoleType, organization_id: int) -> bool:
        """
        指定組織で role 以上の権限を持つかチェック

        - System Admin は organization_id に関わらずバイパスで True
        - 非メンバーは False
        - メンバーなら階層判定 (ADMIN > PROJECT_LEADER > MEMBER)
        """
        if user.is_system_admin:
            return True
        actual = user.get_role_in_organization(organization_id)
        if actual is None:
            return False
        return _role_satisfies(actual, role)

    @staticmethod
    def check_project_access(user: User, project: Project) -> bool:
        """
        プロジェクトへのアクセス権限をチェック

        条件 (いずれか):
        - System Admin
        - 組織内 ADMIN / PROJECT_LEADER (組織内全プロジェクト可視)
        - 組織内 MEMBER かつ project.members に含まれる
        """
        if user.is_system_admin:
            return True
        actual = user.get_role_in_organization(project.organization_id)
        if actual is None:
            return False
        if actual in (RoleType.ADMIN.value, RoleType.PROJECT_LEADER.value):
            return True
        return user in project.members

    @staticmethod
    def check_project_permission(user: User, project: Project, required_role: RoleType) -> bool:
        """
        プロジェクト内での特定ロール権限をチェック

        check_project_access 通過後、has_role で組織内ロールを階層判定する。
        """
        if user.is_system_admin:
            return True
        if not PermissionChecker.check_project_access(user, project):
            return False
        return PermissionChecker.has_role(user, required_role, project.organization_id)


def require_role(roles: List[RoleType]):
    """
    ロールベースのアクセス制御デコレータ (TenantContext ベース)

    使用例:
        @router.get("/admin/users")
        @require_role([RoleType.ADMIN])
        async def list_users(
            tenant: TenantContext = Depends(get_tenant_context),
        ):
            ...

    動作仕様:
        1. tenant (TenantContext) または current_user (User) を kwargs から取得
        2. user.is_system_admin → バイパスで通過
        3. tenant.active_org_id が必須 (System Admin 以外)
        4. 指定 roles のいずれかを満たせば通過、なければ 403

    Raises:
        HTTPException(401): 認証情報がない
        HTTPException(403): 組織コンテキスト不足 or ロール不足
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tenant: Optional[TenantContext] = kwargs.get("tenant")
            current_user: Optional[User] = kwargs.get("current_user")

            user = tenant.user if tenant else current_user
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="認証が必要です",
                )

            # System Admin はバイパス
            if user.is_system_admin:
                return await func(*args, **kwargs)

            org_id: Optional[int] = tenant.active_org_id if tenant else None
            if org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="組織コンテキストが必要です",
                )

            for role in roles:
                if PermissionChecker.has_role(user, role, org_id):
                    return await func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この操作を実行する権限がありません",
            )

        return wrapper

    return decorator
