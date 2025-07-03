"""
プロジェクト分析API

プロジェクトの健康度、ボトルネック、パフォーマンス指標を
提供するAPIエンドポイントです。
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from app.models.user import User
from app.models.project import Project
from app.models.task import TaskStatus
from app.services.analytics_service import analytics_service
from app.core.cache import cache_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/project/{project_id}/health")
@cache_response(prefix="project_health", expire=300)  # 5分間キャッシュ
async def get_project_health(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクトの健康度を取得
    
    プロジェクトの総合的な健康度スコアと、
    タスクの完了率、期限遵守率などの詳細情報を提供します。
    
    Args:
        project: プロジェクト
        db: データベースセッション
        current_user: 現在のユーザー
        
    Returns:
        健康度情報
    """
    try:
        health_data = analytics_service.get_project_health(project.id, db)
        return {
            "project_id": project.id,
            "project_name": project.name,
            **health_data
        }
    except Exception as e:
        logger.error(f"Failed to get project health: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="プロジェクト健康度の取得に失敗しました"
        )


@router.get("/project/{project_id}/bottlenecks")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_bottlenecks(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    プロジェクトのボトルネックを検出
    
    長期間滞留しているタスク、特定メンバーへのタスク集中、
    期限切れタスクなどのボトルネックを検出します。
    
    Args:
        project: プロジェクト
        db: データベースセッション
        current_user: 現在のユーザー
        
    Returns:
        ボトルネック情報のリスト
    """
    try:
        bottlenecks = analytics_service.get_bottlenecks(project.id, db)
        return bottlenecks
    except Exception as e:
        logger.error(f"Failed to detect bottlenecks: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ボトルネック検出に失敗しました"
        )


@router.get("/project/{project_id}/velocity")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_velocity(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user),
    period_days: int = 30
) -> List[Dict[str, Any]]:
    """
    プロジェクトのベロシティトレンドを取得
    
    指定期間の日別完了タスク数を取得します。
    
    Args:
        project: プロジェクト
        db: データベースセッション
        current_user: 現在のユーザー
        period_days: 分析期間（デフォルト30日）
        
    Returns:
        日別ベロシティデータ
    """
    try:
        velocity_data = analytics_service.get_velocity_trend(
            project.id, db, period_days
        )
        return velocity_data
    except Exception as e:
        logger.error(f"Failed to get velocity trend: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ベロシティデータの取得に失敗しました"
        )


@router.get("/project/{project_id}/cycle-time")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_cycle_time(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクトのサイクルタイム分析を取得
    
    各ステータスでのタスクの平均滞留時間を分析します。
    
    Args:
        project: プロジェクト
        db: データベースセッション
        current_user: 現在のユーザー
        
    Returns:
        サイクルタイム分析データ
    """
    try:
        cycle_time_data = analytics_service.get_cycle_time_analysis(project.id, db)
        return {
            "project_id": project.id,
            "project_name": project.name,
            **cycle_time_data
        }
    except Exception as e:
        logger.error(f"Failed to get cycle time analysis: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サイクルタイム分析の取得に失敗しました"
        )


@router.get("/personal/dashboard")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_dashboard(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    period_days: int = 30
) -> Dict[str, Any]:
    """
    個人ダッシュボードデータを取得
    
    現在のユーザーの個人的な生産性指標を取得します。
    完了タスク数、平均処理時間、進行中タスク数、作業フロー分析、
    生産性トレンド、スキルマトリックスを含みます。
    
    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        period_days: 分析期間（デフォルト30日）
        
    Returns:
        個人ダッシュボードデータ
    """
    try:
        from app.models.task import Task, TaskStatus
        from sqlalchemy import func, case, and_
        from datetime import datetime, timedelta
        
        # 基本統計を一度に取得
        stats = db.query(
            func.count(Task.id).label('total'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed'),
            func.sum(case((Task.status == TaskStatus.IN_PROGRESS, 1), else_=0)).label('in_progress'),
            func.sum(case((and_(Task.due_date < datetime.now(), 
                               Task.status != TaskStatus.CLOSED), 1), else_=0)).label('overdue')
        ).filter(Task.assignee_id == current_user.id).first()
        
        total_tasks = stats.total or 0
        completed_tasks = stats.completed or 0
        in_progress_tasks = stats.in_progress or 0
        overdue_tasks = stats.overdue or 0
        
        # 平均処理時間を計算（完了タスクのみ）
        avg_completion_time = db.query(
            func.avg(
                func.extract('epoch', Task.completed_date - Task.created_at) / 86400
            )
        ).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date.isnot(None)
        ).scalar()
        
        # 各ステータスでの滞留時間（作業フロー分析）
        # ユーザーのプロジェクトからステータス情報を取得
        from app.models.project import Project, project_members
        from app.models.auth import OAuthToken
        from app.services.backlog_client import backlog_client
        
        user_projects = db.query(Project).join(project_members).filter(
            project_members.c.user_id == current_user.id
        ).all()
        
        # ステータスIDと名前のマッピングを作成
        status_name_map = {}
        oauth_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == current_user.id,
            OAuthToken.provider == "backlog"
        ).first()
        
        if oauth_token and user_projects:
            for project in user_projects:
                try:
                    statuses = await backlog_client.get_issue_statuses(
                        project_id=project.backlog_id,
                        access_token=oauth_token.access_token
                    )
                    for status in statuses:
                        # ステータス名をキーにしてマッピング（大文字小文字を無視）
                        status_name_map[status['name'].upper()] = status['name']
                        # IDベースのマッピングも作成
                        status_name_map[str(status['id'])] = status['name']
                except Exception as e:
                    logger.warning(f"Failed to get statuses for project {project.id}: {str(e)}")
        
        # デフォルトのステータス名マッピング
        default_status_names = {
            'TODO': '未対応',
            'IN_PROGRESS': '処理中',
            'RESOLVED': '処理済み',
            'CLOSED': '完了'
        }
        
        workflow_analysis = []
        for task_status in TaskStatus:
            if task_status == TaskStatus.CLOSED:
                # 完了タスクは作成から完了までの時間
                avg_time = db.query(
                    func.avg(
                        func.extract('epoch', Task.completed_date - Task.created_at) / 86400
                    )
                ).filter(
                    Task.assignee_id == current_user.id,
                    Task.status == task_status,
                    Task.completed_date.isnot(None)
                ).scalar()
            else:
                # 未完了タスクは更新日からの経過時間
                avg_time = db.query(
                    func.avg(
                        func.extract('epoch', datetime.now() - Task.updated_at) / 86400
                    )
                ).filter(
                    Task.assignee_id == current_user.id,
                    Task.status == task_status
                ).scalar()
            
            # ステータス名を取得（カスタムステータス名があればそれを使用）
            status_value = task_status.value
            status_display_name = status_name_map.get(status_value.upper(), 
                                                     default_status_names.get(status_value, status_value))
            
            workflow_analysis.append({
                "status": status_value,
                "status_name": status_display_name,
                "average_days": round(avg_time, 1) if avg_time else 0
            })
        
        # 生産性トレンド（期間内の日別完了タスク数）
        start_date = datetime.now() - timedelta(days=period_days)
        productivity_trend = db.query(
            func.date(Task.completed_date).label('date'),
            func.count(Task.id).label('completed_count')
        ).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date
        ).group_by(func.date(Task.completed_date)).all()
        
        trend_data = [
            {
                "date": date.isoformat() if date else None,
                "completed_count": count
            }
            for date, count in productivity_trend
        ]
        
        # スキルマトリックス（タスクタイプ別の処理効率）
        skill_matrix = db.query(
            Task.issue_type_name,
            func.count(Task.id).label('count'),
            func.avg(
                case(
                    (Task.status == TaskStatus.CLOSED,
                     func.extract('epoch', Task.completed_date - Task.created_at) / 86400),
                    else_=None
                )
            ).label('avg_completion_days')
        ).filter(
            Task.assignee_id == current_user.id
        ).group_by(Task.issue_type_name).all()
        
        skill_data = []
        for issue_type_name, count, avg_days in skill_matrix:
            if issue_type_name:
                skill_data.append({
                    "task_type": issue_type_name,
                    "total_count": count,
                    "average_completion_days": round(avg_days, 1) if avg_days else None
                })
        
        # 最近完了したタスク（関連データをeager loading）
        recent_completed = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee)
        ).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.CLOSED
        ).order_by(Task.completed_date.desc()).limit(5).all()
        
        return {
            "user_id": current_user.id,
            "user_name": current_user.name,
            "kpi_summary": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                "average_completion_days": round(avg_completion_time, 1) if avg_completion_time else 0
            },
            "workflow_analysis": workflow_analysis,
            "productivity_trend": trend_data,
            "skill_matrix": skill_data,
            "recent_completed_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "project_name": task.project.name if task.project else None,
                    "completed_date": task.completed_date.isoformat() if task.completed_date else None
                }
                for task in recent_completed
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal dashboard: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="個人ダッシュボードデータの取得に失敗しました"
        )


@router.get("/personal/tasks")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_tasks(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    task_status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    個人のタスク一覧を取得
    
    現在のユーザーに割り当てられているタスクの一覧を取得します。
    ステータスによるフィルタリング、ページネーションに対応。
    
    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        status: フィルタリングするタスクステータス（オプション）
        limit: 取得件数の上限
        offset: オフセット
        
    Returns:
        タスク一覧と関連情報
    """
    try:
        from app.models.task import Task, TaskStatus
        
        # クエリ構築
        query = db.query(Task).options(
            joinedload(Task.project),
            joinedload(Task.assignee),
            joinedload(Task.reporter)
        ).filter(Task.assignee_id == current_user.id)
        
        # ステータスフィルタ
        if task_status:
            query = query.filter(Task.status == task_status)
        
        # 総件数を取得
        total_count = query.count()
        
        # タスク一覧を取得（優先度と期限でソート）
        tasks = query.order_by(
            Task.priority.desc(),
            Task.due_date.asc()
        ).limit(limit).offset(offset).all()
        
        # ステータス別集計
        status_summary = db.query(
            Task.status,
            func.count(Task.id)
        ).filter(
            Task.assignee_id == current_user.id
        ).group_by(Task.status).all()
        
        status_counts = {task_status.value: 0 for task_status in TaskStatus}
        for task_status, count in status_summary:
            status_counts[task_status.value] = count
        
        return {
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority,
                    "task_type": task.issue_type_name,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "completed_date": task.completed_date.isoformat() if task.completed_date else None,
                    "project": {
                        "id": task.project.id,
                        "name": task.project.name
                    } if task.project else None,
                    "reporter": {
                        "id": task.reporter.id,
                        "name": task.reporter.name
                    } if task.reporter else None
                }
                for task in tasks
            ],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "status_summary": status_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal tasks: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="個人タスク一覧の取得に失敗しました"
        )


@router.get("/personal/performance")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_performance(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    period_days: int = 90
) -> Dict[str, Any]:
    """
    個人のパフォーマンス指標を取得
    
    指定期間の個人パフォーマンス詳細データを取得します。
    週別・月別の完了率、タスクタイプ別効率、時間帯別生産性など。
    
    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        period_days: 分析期間（デフォルト90日）
        
    Returns:
        パフォーマンス指標の詳細
    """
    try:
        from app.models.task import Task, TaskStatus
        from sqlalchemy import func, case, and_, extract
        from datetime import datetime, timedelta
        
        start_date = datetime.now() - timedelta(days=period_days)
        
        # 週別パフォーマンス
        weekly_performance = db.query(
            func.date_trunc('week', Task.completed_date).label('week'),
            func.count(Task.id).label('completed_count'),
            func.avg(
                func.extract('epoch', Task.completed_date - Task.created_at) / 86400
            ).label('avg_completion_days')
        ).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.CLOSED,
            Task.completed_date >= start_date
        ).group_by(func.date_trunc('week', Task.completed_date)).all()
        
        weekly_data = [
            {
                "week": week.isoformat() if week else None,
                "completed_count": count,
                "average_completion_days": round(avg_days, 1) if avg_days else 0
            }
            for week, count, avg_days in weekly_performance
        ]
        
        # タスクタイプ別効率（期間内）
        type_efficiency = db.query(
            Task.issue_type_name,
            func.count(Task.id).label('total_count'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed_count'),
            func.avg(
                case(
                    (Task.status == TaskStatus.CLOSED,
                     func.extract('epoch', Task.completed_date - Task.created_at) / 86400),
                    else_=None
                )
            ).label('avg_completion_days')
        ).filter(
            Task.assignee_id == current_user.id,
            Task.created_at >= start_date
        ).group_by(Task.issue_type_name).all()
        
        type_data = []
        for issue_type_name, total, completed, avg_days in type_efficiency:
            if issue_type_name:
                type_data.append({
                    "task_type": issue_type_name,
                    "total_count": total,
                    "completed_count": completed,
                    "completion_rate": (completed / total * 100) if total > 0 else 0,
                    "average_completion_days": round(avg_days, 1) if avg_days else None
                })
        
        # 優先度別完了率
        priority_performance = db.query(
            Task.priority,
            func.count(Task.id).label('total_count'),
            func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label('completed_count')
        ).filter(
            Task.assignee_id == current_user.id,
            Task.created_at >= start_date
        ).group_by(Task.priority).all()
        
        priority_data = [
            {
                "priority": priority,
                "total_count": total,
                "completed_count": completed,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            }
            for priority, total, completed in priority_performance
        ]
        
        # 期限遵守率
        deadline_performance = db.query(
            func.count(Task.id).label('total_with_deadline'),
            func.sum(
                case(
                    (and_(Task.status == TaskStatus.CLOSED, 
                          Task.completed_date <= Task.due_date), 1),
                    else_=0
                )
            ).label('completed_on_time')
        ).filter(
            Task.assignee_id == current_user.id,
            Task.due_date.isnot(None),
            Task.created_at >= start_date
        ).first()
        
        deadline_adherence_rate = 0
        if deadline_performance.total_with_deadline > 0:
            deadline_adherence_rate = (
                deadline_performance.completed_on_time / 
                deadline_performance.total_with_deadline * 100
            )
        
        return {
            "user_id": current_user.id,
            "user_name": current_user.name,
            "period_days": period_days,
            "weekly_performance": weekly_data,
            "type_efficiency": type_data,
            "priority_performance": priority_data,
            "deadline_adherence": {
                "total_tasks_with_deadline": deadline_performance.total_with_deadline or 0,
                "completed_on_time": deadline_performance.completed_on_time or 0,
                "adherence_rate": round(deadline_adherence_rate, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal performance: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="個人パフォーマンス指標の取得に失敗しました"
        )