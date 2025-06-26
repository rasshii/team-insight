from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_db_session, get_current_active_user, get_current_project
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.models.sync_history import SyncHistory, SyncType, SyncStatus
from app.services.sync_service import sync_service
from app.core.permissions import PermissionChecker, RoleType
from app.core.utils import get_valid_backlog_token

router = APIRouter()


@router.post("/user/tasks")
async def sync_user_tasks(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    token: OAuthToken = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    現在のユーザーのタスクを同期
    
    バックグラウンドでBacklogからタスクデータを取得し、
    ローカルデータベースと同期します。
    """
    
    # バックグラウンドタスクとして同期を実行
    background_tasks.add_task(
        sync_service.sync_user_tasks,
        current_user,
        token.access_token,
        db
    )
    
    return {
        "message": "タスクの同期を開始しました",
        "status": "started"
    }


@router.post("/project/{project_id}/tasks")
async def sync_project_tasks(
    background_tasks: BackgroundTasks,
    project: Project = Depends(get_current_project),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    token: OAuthToken = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    指定されたプロジェクトのタスクを同期
    
    プロジェクトメンバーのみがアクセス可能です。
    """
    
    # バックグラウンドタスクとして同期を実行
    background_tasks.add_task(
        sync_service.sync_project_tasks,
        project,
        token.access_token,
        db,
        current_user
    )
    
    return {
        "message": f"プロジェクト '{project.name}' のタスク同期を開始しました",
        "status": "started",
        "project_id": project.id
    }


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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    token: OAuthToken = Depends(get_valid_backlog_token)
) -> Dict[str, Any]:
    """
    Backlogから全プロジェクトを同期
    
    管理者またはプロジェクトリーダーのみがアクセス可能です。
    """
    # 権限チェック
    permission_checker = PermissionChecker()
    if not (current_user.is_admin or 
            permission_checker.has_role(current_user, RoleType.PROJECT_LEADER)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この操作には管理者またはプロジェクトリーダーの権限が必要です"
        )
    
    # バックグラウンドで全プロジェクトの同期を実行
    background_tasks.add_task(
        sync_service.sync_all_projects,
        current_user,
        token.access_token,
        db
    )
    
    return {
        "message": "全プロジェクトの同期を開始しました",
        "status": "started"
    }


@router.post("/issue/{issue_id}")
async def sync_single_issue(
    issue_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    token: OAuthToken = Depends(get_valid_backlog_token)
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


@router.get("/connection/status")
async def get_connection_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Backlog接続状態を取得
    
    現在の接続状態と最終同期時刻を返します。
    """
    status = await sync_service.get_connection_status(current_user, db)
    return status


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