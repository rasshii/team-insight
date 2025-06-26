"""
プロジェクト分析API

プロジェクトの健康度、ボトルネック、パフォーマンス指標を
提供するAPIエンドポイントです。
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from app.models.user import User
from app.models.project import Project
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="サイクルタイム分析の取得に失敗しました"
        )


@router.get("/personal/dashboard")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_dashboard(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session)
) -> Dict[str, Any]:
    """
    個人ダッシュボードデータを取得
    
    現在のユーザーの個人的な生産性指標を取得します。
    
    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        
    Returns:
        個人ダッシュボードデータ
    """
    try:
        from app.models.task import Task, TaskStatus
        from sqlalchemy import func
        
        # 個人のタスク統計
        total_tasks = db.query(func.count(Task.id)).filter(
            Task.assignee_id == current_user.id
        ).scalar()
        
        completed_tasks = db.query(func.count(Task.id)).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.CLOSED
        ).scalar()
        
        in_progress_tasks = db.query(func.count(Task.id)).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.IN_PROGRESS
        ).scalar()
        
        overdue_tasks = db.query(func.count(Task.id)).filter(
            Task.assignee_id == current_user.id,
            Task.due_date < func.now(),
            Task.status != TaskStatus.CLOSED
        ).scalar()
        
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
            "statistics": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "overdue_tasks": overdue_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "recent_completed_tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "completed_date": task.completed_date.isoformat() if task.completed_date else None
                }
                for task in recent_completed
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get personal dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="個人ダッシュボードデータの取得に失敗しました"
        )