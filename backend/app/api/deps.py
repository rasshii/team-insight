"""
API依存関係の定義

このモジュールは、FastAPIのDependency Injectionで使用される
共通の依存関係を定義します。
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Path, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.models.project import Project
from app.models.rbac import UserRole
from app.models.auth import OAuthToken
from app.core.permissions import PermissionChecker, RoleType

# OAuth2スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """
    データベースセッションを取得する依存関係

    Yields:
        Session: SQLAlchemyセッション
    """
    yield from get_db()


async def get_current_user(
    request: Request, token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    現在のユーザーを取得（任意）

    Args:
        request: FastAPIリクエストオブジェクト
        token: JWTトークン（Authorizationヘッダーから）
        db: データベースセッション

    Returns:
        Optional[User]: 現在のユーザー（未認証の場合はNone）
    """
    # まずCookieからトークンを取得を試みる
    if not token:
        token = request.cookies.get("auth_token")

    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except HTTPException:
        return None

    # ユーザーのロール情報をeager loadingで取得
    user = (
        db.query(User).options(joinedload(User.user_roles).joinedload(UserRole.role)).filter(User.id == int(user_id)).first()
    )
    return user


def get_current_active_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """
    現在のアクティブユーザーを取得（必須）

    Args:
        current_user: 現在のユーザー

    Returns:
        User: アクティブなユーザー

    Raises:
        HTTPException: ユーザーが未認証またはアクティブでない場合
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


def get_current_active_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    現在のスーパーユーザーを取得

    Args:
        current_user: 現在のアクティブユーザー

    Returns:
        User: スーパーユーザー

    Raises:
        HTTPException: ユーザーがスーパーユーザーでない場合
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user


def get_project_or_404(
    project_id: int = Path(..., description="プロジェクトID"), db: Session = Depends(get_db_session)
) -> Project:
    """
    プロジェクトを取得（存在しない場合は404エラー）

    Args:
        project_id: プロジェクトID
        db: データベースセッション

    Returns:
        Project: プロジェクト

    Raises:
        HTTPException: プロジェクトが見つからない場合
    """
    # プロジェクトとメンバー情報をeager loadingで取得
    project = db.query(Project).options(joinedload(Project.members)).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"プロジェクト（ID: {project_id}）が見つかりません")
    return project


class ProjectAccessChecker:
    """プロジェクトアクセス権限チェッカー"""

    def __init__(self, required_role: Optional[RoleType] = None):
        self.required_role = required_role

    def __call__(
        self,
        project: Project = Depends(get_project_or_404),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db_session),
    ) -> Project:
        """
        プロジェクトへのアクセス権限をチェック

        Args:
            project: プロジェクト
            current_user: 現在のユーザー
            db: データベースセッション

        Returns:
            Project: アクセス可能なプロジェクト

        Raises:
            HTTPException: アクセス権限がない場合
        """
        # 特定の役割が必要な場合は、check_project_permission を使用
        # （内部で check_project_access もチェックされる）
        if self.required_role:
            if not PermissionChecker.check_project_permission(current_user, project.id, self.required_role, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"このプロジェクトでの{self.required_role.value}権限が必要です",
                )
        else:
            # 役割指定がない場合は、アクセス権限のみをチェック
            if not PermissionChecker.check_project_access(current_user, project.id, db):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="このプロジェクトへのアクセス権限がありません")

        return project


# 便利な依存関係のインスタンス
get_current_project = ProjectAccessChecker()
get_current_project_as_leader = ProjectAccessChecker(RoleType.PROJECT_LEADER)
get_current_project_as_admin = ProjectAccessChecker(RoleType.ADMIN)


async def get_valid_backlog_token(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db_session)
) -> Optional["OAuthToken"]:
    """
    有効なBacklogトークンを取得（期限切れの場合は自動リフレッシュ）

    Args:
        current_user: 現在のユーザー
        db: データベースセッション

    Returns:
        Optional[OAuthToken]: 有効なBacklogトークン（存在しない場合はNone）
    """
    from app.models.auth import OAuthToken
    from app.core.token_refresh import token_refresh_service
    from app.core.config import settings
    from datetime import datetime, timezone

    # OAuthトークンを取得
    token = db.query(OAuthToken).filter(OAuthToken.user_id == current_user.id, OAuthToken.provider == "backlog").first()

    if not token:
        return None

    # トークンの有効期限をチェック
    if token.expires_at:
        # タイムゾーン情報がない場合はUTCとして扱う
        expires_at = token.expires_at.replace(tzinfo=timezone.utc) if token.expires_at.tzinfo is None else token.expires_at
        if expires_at < datetime.now(timezone.utc):
            # トークンが期限切れの場合、リフレッシュを試みる
            space_key = token.backlog_space_key or settings.BACKLOG_SPACE_KEY
            refreshed_token = await token_refresh_service.refresh_token(token, db, space_key)

            if refreshed_token:
                return refreshed_token
            else:
                # リフレッシュに失敗した場合
                return None

    return token
