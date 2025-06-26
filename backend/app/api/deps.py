"""
API依存関係の定義

このモジュールは、FastAPIのDependency Injectionで使用される
共通の依存関係を定義します。
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user as _get_current_user
from sqlalchemy.orm import joinedload
from app.models.user import User
from app.models.project import Project
from app.models.rbac import UserRole
from app.core.permissions import PermissionChecker, RoleType


def get_db_session() -> Generator[Session, None, None]:
    """
    データベースセッションを取得する依存関係
    
    Yields:
        Session: SQLAlchemyセッション
    """
    yield from get_db()


async def get_current_user(
    user: Optional[User] = Depends(_get_current_user),
    db: Session = Depends(get_db_session)
) -> Optional[User]:
    """
    現在のユーザーを取得（任意）
    
    Args:
        user: JWTトークンから取得したユーザー情報
        db: データベースセッション
        
    Returns:
        Optional[User]: 現在のユーザー（未認証の場合はNone）
    """
    if user:
        # ユーザーのロール情報をeager loadingで取得
        user = db.query(User).options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        ).filter(User.id == user.id).first()
    return user


def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_project_or_404(
    project_id: int = Path(..., description="プロジェクトID"),
    db: Session = Depends(get_db_session)
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
    project = db.query(Project).options(
        joinedload(Project.members)
    ).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"プロジェクト（ID: {project_id}）が見つかりません"
        )
    return project


class ProjectAccessChecker:
    """プロジェクトアクセス権限チェッカー"""
    
    def __init__(self, required_role: Optional[RoleType] = None):
        self.required_role = required_role
    
    def __call__(
        self,
        project: Project = Depends(get_project_or_404),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db_session)
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
        # プロジェクトへのアクセス権限をチェック
        if not PermissionChecker.check_project_access(current_user, project.id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="このプロジェクトへのアクセス権限がありません"
            )
        
        # 特定の役割が必要な場合
        if self.required_role:
            if not PermissionChecker.check_project_permission(
                current_user, project.id, self.required_role, db
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"このプロジェクトでの{self.required_role.value}権限が必要です"
                )
        
        return project


# 便利な依存関係のインスタンス
get_current_project = ProjectAccessChecker()
get_current_project_as_leader = ProjectAccessChecker(RoleType.PROJECT_LEADER)
get_current_project_as_admin = ProjectAccessChecker(RoleType.ADMIN)