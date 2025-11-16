from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.api.deps import get_db_session, get_current_active_user, get_current_project
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskResponse, TaskListResponse, TaskFilters
from app.core.response_formatter import ResponseFormatter, get_response_formatter
from app.core.response_builder import ResponseBuilder

router = APIRouter()


@router.get("/")
async def get_tasks(
    project_id: Optional[int] = Query(None, description="プロジェクトIDでフィルタ"),
    status: Optional[TaskStatus] = Query(None, description="ステータスでフィルタ"),
    assignee_id: Optional[int] = Query(None, description="担当者IDでフィルタ"),
    priority: Optional[int] = Query(None, description="優先度でフィルタ"),
    search: Optional[str] = Query(None, description="タイトルと説明で検索"),
    limit: int = Query(100, ge=1, le=500, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    タスク一覧を取得

    ユーザーがアクセス可能なタスクのみを返します。
    """
    query = db.query(Task).options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))

    # ユーザーがアクセス可能なプロジェクトのタスクのみ取得
    if not current_user.is_admin:
        user_project_ids = [p.id for p in current_user.projects]
        query = query.filter(Task.project_id.in_(user_project_ids))

    # フィルタ適用
    if project_id:
        query = query.filter(Task.project_id == project_id)

    if status:
        query = query.filter(Task.status == status)

    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    if priority:
        query = query.filter(Task.priority == priority)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter((Task.title.ilike(search_pattern)) | (Task.description.ilike(search_pattern)))

    # 総件数を取得
    total = query.count()

    # ページネーション
    tasks = query.order_by(Task.updated_at.desc()).offset(offset).limit(limit).all()

    task_list = []
    for task in tasks:
        task_data = {
            "id": task.id,
            "backlog_id": task.backlog_id,
            "backlog_key": task.backlog_key,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if task.status else None,
            "priority": task.priority,
            "issue_type_id": task.issue_type_id,
            "issue_type_name": task.issue_type_name,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "start_date": task.start_date.isoformat() if task.start_date else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_date": task.completed_date.isoformat() if task.completed_date else None,
            "milestone_id": task.milestone_id,
            "milestone_name": task.milestone_name,
            "category_names": task.category_names,
            "version_names": task.version_names,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

        if task.project:
            task_data["project"] = {
                "id": task.project.id,
                "name": task.project.name,
                "project_key": task.project.project_key,
                "backlog_id": task.project.backlog_id,
            }
        else:
            task_data["project"] = None

        if task.assignee:
            task_data["assignee"] = {
                "id": task.assignee.id,
                "name": task.assignee.name,
                "email": task.assignee.email,
                "backlog_id": task.assignee.backlog_id,
            }
        else:
            task_data["assignee"] = None

        if task.reporter:
            task_data["reporter"] = {
                "id": task.reporter.id,
                "name": task.reporter.name,
                "email": task.reporter.email,
                "backlog_id": task.reporter.backlog_id,
            }
        else:
            task_data["reporter"] = None

        task_list.append(task_data)

    return formatter(
        ResponseBuilder.success(
            data={"total": total, "limit": limit, "offset": offset, "tasks": task_list},
            message=f"{len(tasks)}件のタスクを取得しました",
        )
    )


@router.get("/my", response_model=TaskListResponse)
async def get_my_tasks(
    status: Optional[TaskStatus] = Query(None, description="ステータスでフィルタ"),
    project_id: Optional[int] = Query(None, description="プロジェクトIDでフィルタ"),
    days: int = Query(30, description="過去何日分のタスクを取得するか"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> TaskListResponse:
    """
    自分に割り当てられたタスクを取得
    """
    query = (
        db.query(Task)
        .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
        .filter(Task.assignee_id == current_user.id)
    )

    # フィルタ適用
    if status:
        query = query.filter(Task.status == status)

    if project_id:
        query = query.filter(Task.project_id == project_id)

    # 期間フィルタ（更新日ベース）
    if days > 0:
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Task.updated_at >= since)

    tasks = query.order_by(Task.updated_at.desc()).all()

    return TaskListResponse(
        total=len(tasks), limit=len(tasks), offset=0, tasks=[TaskResponse.model_validate(task) for task in tasks]
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db_session)
) -> TaskResponse:
    """
    タスクの詳細を取得
    """
    task = (
        db.query(Task)
        .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
        .filter(Task.id == task_id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="タスクが見つかりません")

    # アクセス権限チェック
    if not current_user.is_admin:
        user_project_ids = [p.id for p in current_user.projects]
        if task.project_id not in user_project_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="このタスクへのアクセス権限がありません")

    return TaskResponse.model_validate(task)


@router.get("/backlog/{backlog_key}", response_model=TaskResponse)
async def get_task_by_backlog_key(
    backlog_key: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db_session)
) -> TaskResponse:
    """
    Backlogキーでタスクを取得
    """
    task = (
        db.query(Task)
        .options(joinedload(Task.project), joinedload(Task.assignee), joinedload(Task.reporter))
        .filter(Task.backlog_key == backlog_key)
        .first()
    )

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="タスクが見つかりません")

    # アクセス権限チェック
    if not current_user.is_admin:
        user_project_ids = [p.id for p in current_user.projects]
        if task.project_id not in user_project_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="このタスクへのアクセス権限がありません")

    return TaskResponse.model_validate(task)


@router.get("/statistics/summary")
async def get_task_statistics(
    project_id: Optional[int] = Query(None, description="プロジェクトIDでフィルタ"),
    days: int = Query(30, description="過去何日分の統計を取得するか"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    タスクの統計情報を取得
    """
    query = db.query(Task)

    # ユーザーがアクセス可能なプロジェクトのタスクのみ
    if not current_user.is_admin:
        user_project_ids = [p.id for p in current_user.projects]
        query = query.filter(Task.project_id.in_(user_project_ids))

    if project_id:
        query = query.filter(Task.project_id == project_id)

    # 期間フィルタ
    since = datetime.utcnow() - timedelta(days=days)

    # ステータス別集計
    status_counts = {}
    for status in TaskStatus:
        count = query.filter(Task.status == status).count()
        status_counts[status.value] = count

    # 完了タスク数（期間内）
    completed_count = query.filter(Task.status == TaskStatus.CLOSED, Task.completed_date >= since).count()

    # 期限超過タスク数
    overdue_count = query.filter(
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.due_date < datetime.utcnow()
    ).count()

    # 優先度別集計
    priority_counts = {}
    for priority in [2, 3, 4]:  # 高、中、低
        count = query.filter(Task.priority == priority).count()
        priority_counts[priority] = count

    return {
        "period_days": days,
        "status_distribution": status_counts,
        "completed_in_period": completed_count,
        "overdue_tasks": overdue_count,
        "priority_distribution": priority_counts,
        "total_tasks": query.count(),
    }
