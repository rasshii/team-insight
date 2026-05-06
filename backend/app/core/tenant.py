"""
テナントコンテキスト管理

マルチテナント基盤の中核となる TenantContext を提供する。
リクエストごとに User と active_org_id をひとまとめにし、Service / Repository / API
レイヤから一貫したテナント情報アクセスを可能にする。

権限判定は二本柱で行う:
- users.is_system_admin: System Admin (テナントバイパス)
- organization_members.role: 組織内ロール (ADMIN / PROJECT_LEADER / MEMBER)
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status

from app.models.organization_member import OrganizationRole
from app.models.user import User

_ROLE_HIERARCHY = {
    OrganizationRole.ADMIN.value: 3,
    OrganizationRole.PROJECT_LEADER.value: 2,
    OrganizationRole.MEMBER.value: 1,
}


@dataclass
class TenantContext:
    """
    現在のリクエストにおけるテナント情報

    属性:
        user: 認証済みユーザー
        active_org_id: ユーザーが現在アクティブにしている組織 ID (JWT 由来)
                       System Admin が組織未選択でアクセスする場合 None もありうる
    """

    user: User
    active_org_id: Optional[int]

    @property
    def is_system_admin(self) -> bool:
        """System Admin (テナントバイパス権限) を持つか"""
        return bool(self.user.is_system_admin)

    def require_org_id(self) -> int:
        """active_org_id を必須として返す。設定されていなければ 400 エラー"""
        if self.active_org_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="組織コンテキストが必要です。組織を選択してください。",
            )
        return self.active_org_id

    def role_in_active_org(self) -> Optional[str]:
        """active_org_id 内での自分のロールを返す (組織未選択 or 非メンバーは None)"""
        if self.active_org_id is None:
            return None
        return self.user.get_role_in_organization(self.active_org_id)

    def has_role(self, required: OrganizationRole) -> bool:
        """
        active_org_id 内で required ロール以上を持つか (階層判定)

        - System Admin はバイパスで常に True
        - active_org_id が None の場合は False (System Admin 以外)
        """
        if self.is_system_admin:
            return True
        actual = self.role_in_active_org()
        if actual is None:
            return False
        return _ROLE_HIERARCHY.get(actual, 0) >= _ROLE_HIERARCHY[required.value]

    def require_role(self, required: OrganizationRole) -> None:
        """required ロール以上を満たさなければ 403 を投げる"""
        if not self.has_role(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required.value} 以上の権限が必要です",
            )

    def is_org_admin(self) -> bool:
        return self.has_role(OrganizationRole.ADMIN)

    def is_project_leader_or_above(self) -> bool:
        return self.has_role(OrganizationRole.PROJECT_LEADER)
