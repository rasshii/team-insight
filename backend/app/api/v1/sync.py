from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
import logging

from app.api.deps import get_db_session, get_current_active_user, get_current_project, get_valid_backlog_token
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.services.sync_service import sync_service
from app.core.permissions import PermissionChecker, RoleType
from app.core.response_builder import ResponseBuilder
from app.core.response_formatter import ResponseFormatter, get_response_formatter
from app.core.token_refresh import token_refresh_service
from app.core.config import settings
from app.core.exceptions import ExternalAPIException
# from app.core.utils import get_valid_backlog_token  # TODO: implement this dependency

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/connection/status")
async def get_connection_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    oauth_token: Optional[OAuthToken] = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    Backlog接続状態を取得する（トークン自動リフレッシュ付き）
    """
    if not oauth_token:
        # トークンが存在しないか、リフレッシュに失敗した場合
        # 元のトークンを確認して適切なメッセージを返す
        existing_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == current_user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if not existing_token:
            return formatter(ResponseBuilder.success(
                data={
                    "connected": False,
                    "message": "Backlogアクセストークンが設定されていません",
                    "status": "no_token",
                    "last_project_sync": None,
                    "last_task_sync": None,
                    "expires_at": None
                }
            ))
        else:
            # トークンは存在するがリフレッシュに失敗した
            return formatter(ResponseBuilder.success(
                data={
                    "connected": False,
                    "message": "Backlogアクセストークンの再認証が必要です",
                    "status": "refresh_failed",
                    "last_project_sync": None,
                    "last_task_sync": None,
                    "expires_at": existing_token.expires_at.isoformat() if existing_token.expires_at else None
                }
            ))
    
    # トークンが有効な場合（自動リフレッシュ済みの場合も含む）
    # 最終同期時刻を取得
    last_project_sync = db.query(SyncHistory).filter(
        SyncHistory.user_id == current_user.id,
        SyncHistory.sync_type == SyncType.ALL_PROJECTS,
        SyncHistory.status == SyncStatus.COMPLETED
    ).order_by(desc(SyncHistory.completed_at)).first()
    
    last_task_sync = db.query(SyncHistory).filter(
        SyncHistory.user_id == current_user.id,
        SyncHistory.sync_type.in_([SyncType.USER_TASKS, SyncType.PROJECT_TASKS]),
        SyncHistory.status == SyncStatus.COMPLETED
    ).order_by(desc(SyncHistory.completed_at)).first()
    
    return formatter(ResponseBuilder.success(
        data={
            "connected": True,
            "message": "Backlogと正常に接続されています",
            "status": "active",
            "last_project_sync": last_project_sync.completed_at.isoformat() if last_project_sync else None,
            "last_task_sync": last_task_sync.completed_at.isoformat() if last_task_sync else None,
            "expires_at": oauth_token.expires_at.isoformat() if oauth_token.expires_at else None
        }
    ))


@router.post("/user/tasks")
async def sync_user_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    oauth_token: Optional[OAuthToken] = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    現在のユーザーのタスクを同期
    
    Backlogからタスクデータを取得し、ローカルデータベースと同期します。
    """
    logger.info(f"sync_user_tasks called by user {current_user.id}")
    
    if not oauth_token:
        logger.error(f"No valid Backlog OAuth token for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogとの連携が設定されていないか、認証が必要です"
        )
    
    try:
        # 同期を実行（同期的に実行）
        result = await sync_service.sync_user_tasks(
            current_user,
            oauth_token.access_token,
            db
        )
        
        logger.info(f"User task sync completed: {result}")
        
        return formatter(ResponseBuilder.success(
            data=result,
            message=f"タスクの同期が完了しました。新規: {result['created']}件、更新: {result['updated']}件"
        ))
    except Exception as e:
        logger.error(f"Failed to sync user tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"タスクの同期中にエラーが発生しました: {str(e)}"
        )


@router.post("/project/{project_id}/tasks")
async def sync_project_tasks(
    project: Project = Depends(get_current_project),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    oauth_token: Optional[OAuthToken] = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    指定されたプロジェクトのタスクを同期
    
    プロジェクトメンバーのみがアクセス可能です。
    """
    logger.info(f"sync_project_tasks called for project {project.id} by user {current_user.id}")
    
    if not oauth_token:
        logger.error(f"No valid Backlog OAuth token for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogとの連携が設定されていないか、認証が必要です"
        )
    
    try:
        # 同期を実行（同期的に実行）
        result = await sync_service.sync_project_tasks(
            project,
            oauth_token.access_token,
            db,
            current_user
        )
        
        logger.info(f"Task sync completed for project {project.id}: {result}")
        
        return formatter(ResponseBuilder.success(
            data=result,
            message=f"タスクの同期が完了しました。新規: {result['created']}件、更新: {result['updated']}件"
        ))
    except Exception as e:
        logger.error(f"Failed to sync project tasks: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"タスクの同期中にエラーが発生しました: {str(e)}"
        )


@router.get("/project/{project_id}/status")
async def get_sync_status(
    project: Project = Depends(get_current_project),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    プロジェクトの同期状況を取得
    
    最後の同期日時やタスク数などの情報を返します。
    """
    status = await sync_service.get_sync_status(project.id, db)
    
    return {
        "project_id": project.id,
        "project_name": project.name,
        **status
    }


@router.post("/projects/all")
async def sync_all_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    oauth_token: Optional[OAuthToken] = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    Backlogから全プロジェクトを同期
    
    管理者またはプロジェクトリーダーのみがアクセス可能です。
    """
    logger.info(f"sync_all_projects called by user {current_user.id} ({current_user.email})")
    
    # 権限チェック
    permission_checker = PermissionChecker()
    if not (current_user.is_admin or 
            permission_checker.has_role(current_user, RoleType.PROJECT_LEADER)):
        logger.warning(f"User {current_user.id} ({current_user.email}) does not have permission to sync projects")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者またはプロジェクトリーダーの権限が必要です"
        )
    
    if not oauth_token:
        logger.error(f"No valid Backlog OAuth token for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogとの連携が設定されていないか、認証が必要です"
            )
    
    logger.info(f"Starting sync with valid token...")
    
    try:
        # 同期を実行（非同期で実行）
        result = await sync_service.sync_all_projects(
            current_user,
            oauth_token.access_token,
            db
        )
        
        logger.info(f"Sync completed successfully for user {current_user.id}: {result}")
        
        return formatter(ResponseBuilder.success(
            data=result,
            message="プロジェクトの同期が完了しました"
        ))
    except Exception as e:
        logger.error(f"Failed to sync projects for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"プロジェクトの同期中にエラーが発生しました: {str(e)}"
        )


@router.post("/issue/{issue_id}")
async def sync_single_issue(
    issue_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    # token: OAuthToken = Depends(get_valid_backlog_token)  # TODO: implement this dependency
) -> Dict[str, Any]:
    """
    単一の課題を同期
    
    特定の課題のみを即座に同期します。
    """
    
    try:
        task = await sync_service.sync_single_issue(
            issue_id,
            token.access_token,
            db
        )
        
        return {
            "message": "課題の同期が完了しました",
            "task": {
                "id": task.id,
                "backlog_key": task.backlog_key,
                "title": task.title,
                "status": task.status.value,
                "updated_at": task.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"課題の同期中にエラーが発生しました: {str(e)}"
        )


@router.get("/history")
async def get_sync_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    sync_type: Optional[SyncType] = Query(None, description="同期タイプでフィルタ"),
    status: Optional[SyncStatus] = Query(None, description="ステータスでフィルタ"),
    days: int = Query(7, description="過去何日分の履歴を取得するか"),
    limit: int = Query(50, description="取得する最大件数"),
    offset: int = Query(0, description="オフセット")
) -> Dict[str, Any]:
    """
    同期履歴を取得
    
    ユーザーの同期履歴を新しい順に返します。
    """
    # 基本クエリ
    query = db.query(SyncHistory).filter(
        SyncHistory.user_id == current_user.id
    )
    
    # 日数フィルタ
    if days > 0:
        since_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(SyncHistory.started_at >= since_date)
    
    # タイプフィルタ
    if sync_type:
        query = query.filter(SyncHistory.sync_type == sync_type)
    
    # ステータスフィルタ
    if status:
        query = query.filter(SyncHistory.status == status)
    
    # 総件数を取得
    total_count = query.count()
    
    # ソートとページネーション
    histories = query.order_by(desc(SyncHistory.started_at)).limit(limit).offset(offset).all()
    
    # レスポンスの構築
    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "histories": [
            {
                "id": h.id,
                "sync_type": h.sync_type.value,
                "status": h.status.value,
                "target_id": h.target_id,
                "target_name": h.target_name,
                "items_created": h.items_created,
                "items_updated": h.items_updated,
                "items_failed": h.items_failed,
                "total_items": h.total_items,
                "error_message": h.error_message,
                "started_at": h.started_at.isoformat() if h.started_at else None,
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                "duration_seconds": h.duration_seconds
            }
            for h in histories
        ]
    }


@router.post("/users/import-from-backlog")
async def import_backlog_users(
    mode: Literal["all", "active_only"] = Query(
        "active_only", 
        description="インポートモード: 'all' - 全ユーザー, 'active_only' - アクティブユーザーのみ"
    ),
    assign_default_role: bool = Query(
        True, 
        description="新規ユーザーにMEMBERロールを自動付与するか"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    oauth_token: Optional[OAuthToken] = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    Backlogから全プロジェクトのユーザーをインポート
    
    管理者権限が必要です。
    Backlogの全プロジェクトからユーザー情報を収集し、
    Team Insightのユーザーとして登録します。
    
    Parameters:
    - mode: "all" - 全ユーザー, "active_only" - アクティブユーザーのみ
    - assign_default_role: Trueの場合、新規ユーザーにMEMBERロールを自動付与
    """
    logger.info(f"import_backlog_users called by user {current_user.id} ({current_user.email})")
    
    # 権限チェック（管理者のみ）
    permission_checker = PermissionChecker()
    if not current_user.is_admin:
        logger.warning(f"User {current_user.id} ({current_user.email}) does not have permission to import users")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者権限が必要です"
        )
    
    if not oauth_token:
        logger.error(f"No valid Backlog OAuth token for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogとの連携が設定されていないか、認証が必要です"
        )
    
    try:
        # ユーザーインポートを実行
        result = await sync_service.import_users_from_backlog(
            current_user,
            oauth_token.access_token,
            db,
            mode=mode,
            assign_default_role=assign_default_role
        )
        
        logger.info(f"User import completed successfully: {result}")
        
        message = f"ユーザーのインポートが完了しました。"
        message += f" 新規: {result['created']}名、更新: {result['updated']}名"
        if result['default_role_assigned']:
            message += " (新規ユーザーにMEMBERロールを付与)"
        
        return formatter(ResponseBuilder.success(
            data=result,
            message=message
        ))
    except Exception as e:
        logger.error(f"Failed to import users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザーのインポート中にエラーが発生しました: {str(e)}"
        )