from typing import List, Optional
from app.models.rbac import UserRole
from app.schemas.auth import UserRoleResponse, RoleResponse
from app.models.auth import OAuthToken
from app.models.user import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from app.api.deps import get_db_session, get_current_active_user
from app.core.token_refresh import token_refresh_service
import logging
import asyncio

logger = logging.getLogger(__name__)


def build_user_role_responses(user_roles: List[UserRole]) -> List[UserRoleResponse]:
    """
    UserRoleオブジェクトのリストをUserRoleResponseのリストに変換
    
    Args:
        user_roles: UserRoleオブジェクトのリスト
        
    Returns:
        UserRoleResponseオブジェクトのリスト
    """
    return [
        UserRoleResponse(
            id=ur.id,
            role_id=ur.role_id,
            project_id=ur.project_id,
            role=RoleResponse(
                id=ur.role.id,
                name=ur.role.name,
                description=ur.role.description
            )
        )
        for ur in user_roles
    ]


async def get_valid_backlog_token(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
) -> OAuthToken:
    """
    ユーザーの有効なBacklog OAuthトークンを取得
    期限切れの場合は自動的にリフレッシュを試みる
    
    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        
    Returns:
        有効なOAuthToken
        
    Raises:
        HTTPException: トークンが見つからないかリフレッシュに失敗した場合
    """
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not token:
        logger.warning(f"Backlog token not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogアクセストークンが見つかりません。再度ログインしてください。"
        )
    
    # トークンが期限切れまたは期限切れ間近の場合はリフレッシュを試みる
    if token.is_expired() or token_refresh_service._should_refresh_token(token):
        logger.info(f"Attempting to refresh Backlog token for user {current_user.id}")
        try:
            refreshed_token = await token_refresh_service.refresh_token(token, db)
            
            if refreshed_token:
                logger.info(f"Successfully refreshed Backlog token for user {current_user.id}")
                return refreshed_token
            else:
                logger.error(f"Failed to refresh Backlog token for user {current_user.id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="アクセストークンのリフレッシュに失敗しました。再度ログインしてください。"
                )
        except Exception as e:
            logger.error(f"Error refreshing Backlog token for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="アクセストークンのリフレッシュに失敗しました。再度ログインしてください。"
            )
    
    return token


class QueryBuilder:
    """データベースクエリビルダーユーティリティ"""
    
    @staticmethod
    def with_user_roles(query):
        """ユーザーロール情報を含めてクエリ"""
        from sqlalchemy.orm import joinedload
        return query.options(
            joinedload(User.user_roles).joinedload(UserRole.role)
        )
    
    @staticmethod
    def with_projects(query):
        """プロジェクト情報を含めてクエリ"""
        from sqlalchemy.orm import joinedload
        return query.options(joinedload(User.projects))
    
    @staticmethod
    def with_all_relations(query):
        """全ての関連情報を含めてクエリ"""
        from sqlalchemy.orm import joinedload
        return query.options(
            joinedload(User.user_roles).joinedload(UserRole.role),
            joinedload(User.projects)
        )
