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
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """
    プロジェクトの健康度を取得

    プロジェクトの総合的な健康度を示す複数の指標を算出し、
    プロジェクトマネージャーがプロジェクトの状態を素早く把握できるようにします。
    健康度スコア、完了率、期限遵守率、アクティブタスク数などを提供します。

    認証:
        - 認証必須（アクティブなユーザーのみ）
        - プロジェクトメンバーのみアクセス可能

    処理フロー:
        1. プロジェクトメンバーであることを確認（依存性注入で自動実行）
        2. analytics_serviceを使用して健康度データを計算
        3. プロジェクト情報と健康度データを統合
        4. レスポンスを返却

    Args:
        project: プロジェクトオブジェクト（依存性注入、権限チェック済み）
        db: データベースセッション（依存性注入）
        current_user: 現在のアクティブユーザー（依存性注入）

    Returns:
        Dict[str, Any]: プロジェクトの健康度情報
        {
            "project_id": 1,
            "project_name": "プロジェクト名",
            "health_score": 85.5,
            "completion_rate": 75.0,
            "on_time_rate": 80.0,
            "active_tasks": 25,
            "overdue_tasks": 3,
            "total_tasks": 100
        }

    Raises:
        HTTPException(500): 健康度の計算に失敗した場合

    Examples:
        リクエスト例:
            GET /api/v1/analytics/project/1/health
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        レスポンス例:
            {
                "project_id": 1,
                "project_name": "Webアプリケーション開発",
                "health_score": 85.5,
                "completion_rate": 75.0,
                "on_time_rate": 80.0,
                "active_tasks": 25,
                "overdue_tasks": 3,
                "total_tasks": 100,
                "average_task_age_days": 5.2
            }

    Note:
        - 健康度スコアは0-100の範囲で、複数の指標を加重平均して算出されます
        - レスポンスは5分間キャッシュされ、パフォーマンスが最適化されています
        - キャッシュキーにはproject_idが含まれます

    キャッシュ戦略:
        - キャッシュプレフィックス: "project_health"
        - キャッシュ有効期限: 300秒（5分）
        - キャッシュキー: "project_health:{project_id}"
        - キャッシュの無効化: プロジェクトのタスクが更新された場合は自動的に無効化
    """
    try:
        health_data = analytics_service.get_project_health(project.id, db)
        return {"project_id": project.id, "project_name": project.name, **health_data}
    except Exception as e:
        logger.error(f"Failed to get project health: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="プロジェクト健康度の取得に失敗しました"
        )


@router.get("/project/{project_id}/bottlenecks")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_bottlenecks(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user),
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
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ボトルネック検出に失敗しました")


@router.get("/project/{project_id}/velocity")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_velocity(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user),
    period_days: int = 30,
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
        velocity_data = analytics_service.get_velocity_trend(project.id, db, period_days)
        return velocity_data
    except Exception as e:
        logger.error(f"Failed to get velocity trend: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ベロシティデータの取得に失敗しました"
        )


@router.get("/project/{project_id}/cycle-time")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_project_cycle_time(
    project: Project = Depends(deps.get_current_project),
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user),
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
        return {"project_id": project.id, "project_name": project.name, **cycle_time_data}
    except Exception as e:
        logger.error(f"Failed to get cycle time analysis: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="サイクルタイム分析の取得に失敗しました"
        )


@router.get("/personal/dashboard")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_dashboard(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    period_days: int = 30,
) -> Dict[str, Any]:
    """
    個人ダッシュボードデータを取得

    ユーザー個人の生産性とパフォーマンスを可視化するための
    包括的なダッシュボードデータを提供します。KPI集計、作業フロー分析、
    生産性トレンド、スキルマトリックス、最近完了したタスクなどが含まれます。

    認証:
        - 認証必須（アクティブなユーザーのみ）

    処理フロー:
        1. DashboardServiceを初期化
        2. ダッシュボードデータを取得（Service層に委譲）
        3. レスポンスを返却

    Args:
        current_user: 現在のアクティブユーザー（依存性注入）
        db: データベースセッション（依存性注入）
        period_days: 分析対象期間（日数、デフォルト: 30日）

    Returns:
        Dict[str, Any]: 個人ダッシュボードの包括的なデータ
        {
            "user_id": 1,
            "user_name": "ユーザー名",
            "kpi_summary": {
                "total_tasks": 100,
                "completed_tasks": 75,
                "in_progress_tasks": 20,
                "overdue_tasks": 5,
                "completion_rate": 75.0,
                "average_completion_days": 3.5
            },
            "workflow_analysis": [
                {
                    "status": "TODO",
                    "status_name": "未対応",
                    "average_days": 2.1
                },
                ...
            ],
            "productivity_trend": [
                {
                    "date": "2025-01-15",
                    "completed_count": 5
                },
                ...
            ],
            "skill_matrix": [
                {
                    "task_type": "バグ",
                    "total_count": 20,
                    "average_completion_days": 2.5
                },
                ...
            ],
            "recent_completed_tasks": [...]
        }

    Raises:
        HTTPException(500): ダッシュボードデータの取得に失敗した場合

    Examples:
        リクエスト例1（デフォルト30日間）:
            GET /api/v1/analytics/personal/dashboard
            Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        リクエスト例2（過去90日間を指定）:
            GET /api/v1/analytics/personal/dashboard?period_days=90

        レスポンス例:
            {
                "user_id": 1,
                "user_name": "山田太郎",
                "kpi_summary": {
                    "total_tasks": 100,
                    "completed_tasks": 75,
                    "in_progress_tasks": 20,
                    "overdue_tasks": 5,
                    "completion_rate": 75.0,
                    "average_completion_days": 3.5
                },
                "workflow_analysis": [
                    {
                        "status": "TODO",
                        "status_name": "未対応",
                        "average_days": 2.1
                    },
                    {
                        "status": "IN_PROGRESS",
                        "status_name": "処理中",
                        "average_days": 1.8
                    }
                ],
                "productivity_trend": [
                    {
                        "date": "2025-01-15",
                        "completed_count": 5
                    }
                ],
                "skill_matrix": [
                    {
                        "task_type": "バグ",
                        "total_count": 20,
                        "average_completion_days": 2.5
                    }
                ],
                "recent_completed_tasks": [
                    {
                        "id": 123,
                        "title": "ログイン機能のバグ修正",
                        "project_name": "Webアプリ開発",
                        "completed_date": "2025-01-15T10:30:00"
                    }
                ]
            }

    Note:
        - レスポンスは5分間キャッシュされ、頻繁なアクセスでもパフォーマンスが保たれます
        - ビジネスロジックはDashboardServiceに委譲され、API層はシンプルに保たれます
        - Service層の導入により、テスタビリティと保守性が向上しています

    キャッシュ戦略:
        - キャッシュプレフィックス: "analytics"
        - キャッシュ有効期限: 300秒（5分）
        - キャッシュキー: "analytics:{user_id}:personal_dashboard:{period_days}"
    """
    try:
        from app.services.dashboard_service import DashboardService

        # DashboardServiceを初期化してダッシュボードデータを取得
        dashboard_service = DashboardService(db, current_user.id)
        data = await dashboard_service.get_personal_dashboard_data(period_days=period_days, user=current_user)

        return data

    except Exception as e:
        logger.error(f"Failed to get personal dashboard: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="個人ダッシュボードデータの取得に失敗しました"
        )


@router.get("/personal/tasks")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_tasks(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    task_status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    個人のタスク一覧を取得

    現在のユーザーに割り当てられているタスクの一覧を取得します。
    ステータスによるフィルタリング、ページネーションに対応。

    認証:
        - 認証必須（アクティブなユーザーのみ）

    処理フロー:
        1. TaskServiceを初期化
        2. タスク一覧を取得（Service層に委譲）
        3. レスポンスを返却

    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        task_status: フィルタリングするタスクステータス（オプション）
        limit: 取得件数の上限（デフォルト: 50）
        offset: オフセット（デフォルト: 0）

    Returns:
        タスク一覧と関連情報
        {
            "tasks": [
                {
                    "id": int,
                    "title": str,
                    "description": str,
                    "status": str,
                    "priority": int,
                    "task_type": str,
                    "due_date": str (ISO format) または None,
                    "created_at": str (ISO format),
                    "updated_at": str (ISO format),
                    "completed_date": str (ISO format) または None,
                    "project": {
                        "id": int,
                        "name": str
                    } または None,
                    "reporter": {
                        "id": int,
                        "name": str
                    } または None
                },
                ...
            ],
            "pagination": {
                "total": int,
                "limit": int,
                "offset": int,
                "has_more": bool
            },
            "status_summary": {
                "TODO": int,
                "IN_PROGRESS": int,
                "RESOLVED": int,
                "CLOSED": int
            }
        }

    Raises:
        HTTPException(500): タスク一覧の取得に失敗した場合

    Note:
        - ビジネスロジックはTaskServiceに委譲され、API層はシンプルに保たれます
        - Service層の導入により、テスタビリティと保守性が向上しています
    """
    try:
        from app.services.task_service import TaskService

        # TaskServiceを初期化してタスク一覧を取得
        task_service = TaskService(db)
        result = task_service.get_user_tasks(user_id=current_user.id, status=task_status, skip=offset, limit=limit)

        return result

    except Exception as e:
        logger.error(f"Failed to get personal tasks: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="個人タスク一覧の取得に失敗しました"
        )


@router.get("/personal/performance")
@cache_response(prefix="analytics", expire=300)  # 5分間キャッシュ
async def get_personal_performance(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    period_days: int = 90,
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
        weekly_performance = (
            db.query(
                func.date_trunc("week", Task.completed_date).label("week"),
                func.count(Task.id).label("completed_count"),
                func.avg(func.extract("epoch", Task.completed_date - Task.created_at) / 86400).label("avg_completion_days"),
            )
            .filter(Task.assignee_id == current_user.id, Task.status == TaskStatus.CLOSED, Task.completed_date >= start_date)
            .group_by(func.date_trunc("week", Task.completed_date))
            .all()
        )

        weekly_data = [
            {
                "week": week.isoformat() if week else None,
                "completed_count": count,
                "average_completion_days": round(avg_days, 1) if avg_days else 0,
            }
            for week, count, avg_days in weekly_performance
        ]

        # タスクタイプ別効率（期間内）
        type_efficiency = (
            db.query(
                Task.issue_type_name,
                func.count(Task.id).label("total_count"),
                func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label("completed_count"),
                func.avg(
                    case(
                        (
                            Task.status == TaskStatus.CLOSED,
                            func.extract("epoch", Task.completed_date - Task.created_at) / 86400,
                        ),
                        else_=None,
                    )
                ).label("avg_completion_days"),
            )
            .filter(Task.assignee_id == current_user.id, Task.created_at >= start_date)
            .group_by(Task.issue_type_name)
            .all()
        )

        type_data = []
        for issue_type_name, total, completed, avg_days in type_efficiency:
            if issue_type_name:
                type_data.append(
                    {
                        "task_type": issue_type_name,
                        "total_count": total,
                        "completed_count": completed,
                        "completion_rate": (completed / total * 100) if total > 0 else 0,
                        "average_completion_days": round(avg_days, 1) if avg_days else None,
                    }
                )

        # 優先度別完了率
        priority_performance = (
            db.query(
                Task.priority,
                func.count(Task.id).label("total_count"),
                func.sum(case((Task.status == TaskStatus.CLOSED, 1), else_=0)).label("completed_count"),
            )
            .filter(Task.assignee_id == current_user.id, Task.created_at >= start_date)
            .group_by(Task.priority)
            .all()
        )

        priority_data = [
            {
                "priority": priority,
                "total_count": total,
                "completed_count": completed,
                "completion_rate": (completed / total * 100) if total > 0 else 0,
            }
            for priority, total, completed in priority_performance
        ]

        # 期限遵守率
        deadline_performance = (
            db.query(
                func.count(Task.id).label("total_with_deadline"),
                func.sum(
                    case((and_(Task.status == TaskStatus.CLOSED, Task.completed_date <= Task.due_date), 1), else_=0)
                ).label("completed_on_time"),
            )
            .filter(Task.assignee_id == current_user.id, Task.due_date.isnot(None), Task.created_at >= start_date)
            .first()
        )

        deadline_adherence_rate = 0
        if deadline_performance.total_with_deadline > 0:
            deadline_adherence_rate = deadline_performance.completed_on_time / deadline_performance.total_with_deadline * 100

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
                "adherence_rate": round(deadline_adherence_rate, 1),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get personal performance: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="個人パフォーマンス指標の取得に失敗しました"
        )
