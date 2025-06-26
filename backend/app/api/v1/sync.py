from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.deps import get_db_session, get_current_active_user, get_current_project
from app.models.user import User
from app.models.project import Project
from app.models.auth import OAuthToken
from app.services.sync_service import sync_service
from app.core.permissions import PermissionChecker, RoleType

router = APIRouter()


@router.post("/user/tasks")
async def sync_user_tasks(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    現在のユーザーのタスクを同期
    
    バックグラウンドでBacklogからタスクデータを取得し、
    ローカルデータベースと同期します。
    """
    # ユーザーのアクセストークンを取得
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogアクセストークンが見つかりません。再度ログインしてください。"
        )
    
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アクセストークンの有効期限が切れています。再度ログインしてください。"
        )
    
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
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    指定されたプロジェクトのタスクを同期
    
    プロジェクトメンバーのみがアクセス可能です。
    """
    # ユーザーのアクセストークンを取得
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogアクセストークンが見つかりません。再度ログインしてください。"
        )
    
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アクセストークンの有効期限が切れています。再度ログインしてください。"
        )
    
    # バックグラウンドタスクとして同期を実行
    background_tasks.add_task(
        sync_service.sync_project_tasks,
        project,
        token.access_token,
        db
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
async def sync_all_user_projects(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    ユーザーが参加している全プロジェクトのタスクを同期
    
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
    
    # ユーザーのアクセストークンを取得
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogアクセストークンが見つかりません。再度ログインしてください。"
        )
    
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アクセストークンの有効期限が切れています。再度ログインしてください。"
        )
    
    # ユーザーが参加しているプロジェクトを取得
    projects = current_user.projects
    
    # 各プロジェクトの同期をバックグラウンドで実行
    for project in projects:
        background_tasks.add_task(
            sync_service.sync_project_tasks,
            project,
            token.access_token,
            db
        )
    
    return {
        "message": f"{len(projects)} 個のプロジェクトの同期を開始しました",
        "status": "started",
        "project_count": len(projects),
        "projects": [{"id": p.id, "name": p.name} for p in projects]
    }


@router.post("/issue/{issue_id}")
async def sync_single_issue(
    issue_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    単一の課題を同期
    
    特定の課題のみを即座に同期します。
    """
    # ユーザーのアクセストークンを取得
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backlogアクセストークンが見つかりません。再度ログインしてください。"
        )
    
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アクセストークンの有効期限が切れています。再度ログインしてください。"
        )
    
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