"""
API 依存関係の定義 (Phase 0: マルチテナント対応)

FastAPI の Dependency Injection で使用される共通の依存関係を定義する。

主要な依存関係:
- get_db_session: DB セッション
- get_current_user: 現在のユーザー (オプショナル認証)
- get_current_active_user: 現在のアクティブユーザー (認証必須)
- get_current_active_superuser: System Admin / superuser のみ
- get_tenant_context: 認証済ユーザー + active_org_id を含む TenantContext
- get_project_or_404: プロジェクト取得
- ProjectAccessChecker: プロジェクトアクセス権チェック
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload

from app.core.permissions import PermissionChecker, RoleType
from app.core.security import decode_token
from app.core.tenant import TenantContext
from app.db.session import get_db
from app.models.organization_member import OrganizationMember
from app.models.project import Project
from app.models.user import User

# OAuth2 スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """データベースセッションを取得する依存関係"""
    yield from get_db()


def _extract_token(request: Request, header_token: Optional[str]) -> Optional[str]:
    """Authorization ヘッダー → Cookie の優先順位でトークンを取り出す"""
    if header_token:
        return header_token
    return request.cookies.get("auth_token")


def _ensure_jwt_payload(request: Request, token: Optional[str]) -> Optional[dict]:
    """
    JWT payload を取得 (1 リクエスト 1 デコードに保つため state にキャッシュ)
    """
    if hasattr(request.state, "jwt_payload"):
        return request.state.jwt_payload

    actual_token = _extract_token(request, token)
    if not actual_token:
        request.state.jwt_payload = None
        return None

    try:
        payload = decode_token(actual_token)
    except HTTPException:
        request.state.jwt_payload = None
        return None

    request.state.jwt_payload = payload
    return payload


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> Optional[User]:
    """
    現在のユーザーを取得する (オプショナル認証)

    JWT を検証してユーザーを取得する。
    organization_memberships を eager load し、Phase 0 の権限判定で N+1 を回避する。
    """
    payload = _ensure_jwt_payload(request, token)
    if not payload:
        return None

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        return None

    user = (
        db.query(User)
        .options(
            joinedload(User.organization_memberships).joinedload(
                OrganizationMember.organization
            )
        )
        .filter(User.id == int(user_id_str))
        .first()
    )
    return user


def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """現在のアクティブユーザーを取得する (認証必須)"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="非アクティブなユーザーです"
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    System Admin (or legacy superuser) を取得する

    Phase 0: is_system_admin または is_superuser のいずれかが True なら通過。
    """
    if not (current_user.is_system_admin or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="権限が不足しています"
        )
    return current_user


def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> TenantContext:
    """
    認証済ユーザー + JWT 由来の active_org_id を含む TenantContext を返す

    Service / API レイヤから一貫したテナント情報アクセスを可能にする。
    """
    payload = _ensure_jwt_payload(request, None) or {}
    active_org_id = payload.get("active_org_id")
    return TenantContext(user=current_user, active_org_id=active_org_id)


def get_project_or_404(
    project_id: int = Path(..., description="プロジェクトID"),
    db: Session = Depends(get_db_session),
) -> Project:
    """プロジェクトを取得する (見つからなければ 404)"""
    project = (
        db.query(Project)
        .options(joinedload(Project.members))
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"プロジェクト (ID: {project_id}) が見つかりません",
        )
    return project


class ProjectAccessChecker:
    """
    プロジェクトアクセス権限チェッカー (Phase 0: project ベース)

    使用例:
        @router.get("/projects/{project_id}")
        async def get_project(
            project: Project = Depends(get_current_project),
            tenant: TenantContext = Depends(get_tenant_context),
        ):
            ...
    """

    def __init__(self, required_role: Optional[RoleType] = None):
        self.required_role = required_role

    def __call__(
        self,
        project: Project = Depends(get_project_or_404),
        current_user: User = Depends(get_current_active_user),
        tenant: TenantContext = Depends(get_tenant_context),
    ) -> Project:
        # System Admin はバイパス
        if current_user.is_system_admin:
            return project

        # 組織コンテキストとプロジェクトの組織が一致することが必須
        if (
            tenant.active_org_id is not None
            and tenant.active_org_id != project.organization_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"プロジェクト (ID: {project.id}) が見つかりません",
            )

        if self.required_role:
            if not PermissionChecker.check_project_permission(
                current_user, project, self.required_role
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"このプロジェクトでの{self.required_role.value}権限が必要です",
                )
        else:
            if not PermissionChecker.check_project_access(current_user, project):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="このプロジェクトへのアクセス権限がありません",
                )

        return project


# 便利な依存関係のインスタンス
get_current_project = ProjectAccessChecker()
get_current_project_as_leader = ProjectAccessChecker(RoleType.PROJECT_LEADER)
get_current_project_as_admin = ProjectAccessChecker(RoleType.ADMIN)
