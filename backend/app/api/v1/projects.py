"""
プロジェクト管理API

このモジュールは、プロジェクト情報の取得と管理機能を提供します。
キャッシュ機能を活用して、データベースへの負荷を軽減します。
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.core.query_optimizer import QueryOptimizer
from app.api import deps
from datetime import timedelta
from app.models.project import Project
from app.schemas.project import Project as ProjectSchema, ProjectUpdate
from app.core.cache import cache_response, cache_invalidate
from app.models.user import User
from app.core.deps import get_response_formatter
from app.core.response_builder import ResponseFormatter
from app.core.exceptions import NotFoundException, ExternalAPIException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def get_projects(
    db: Session = Depends(deps.get_db_session),
    current_user: User = Depends(deps.get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    現在のユーザーが参加しているプロジェクト一覧を取得

    Args:
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト一覧
    """
    # ユーザーが参加しているプロジェクトを取得（リレーションシップを含む）
    logger.info(f"Fetching projects for user {current_user.id}")

    # 最適化されたクエリを使用
    user_with_projects = (
        db.query(User)
        .options(joinedload(User.projects).joinedload(Project.members))
        .filter(User.id == current_user.id)
        .first()
    )
    projects = user_with_projects.projects if user_with_projects else []

    logger.info(f"Found {len(projects)} projects for user {current_user.id}")
    if projects:
        logger.info(f"Project IDs: {[p.id for p in projects]}")
        logger.info(f"Project keys: {[p.project_key for p in projects]}")

    # Pydanticスキーマに変換
    projects_data = [ProjectSchema.model_validate(p).model_dump() for p in projects]

    return formatter.success(data={"projects": projects_data}, message=f"{len(projects_data)}件のプロジェクトを取得しました")


@router.get("/{project_id}")
def get_project_detail(
    project: Project = Depends(deps.get_current_project),
    current_user: User = Depends(deps.get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    プロジェクト詳細を取得します

    権限チェック：プロジェクトメンバーのみアクセス可能

    Args:
        project: プロジェクト（権限チェック済み）
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト詳細情報
    """
    logger.info(f"プロジェクト詳細取得: プロジェクトID {project.id}, ユーザー {current_user.email}")

    # Pydanticスキーマに変換
    project_data = ProjectSchema.model_validate(project).model_dump()

    return formatter.success(data=project_data, message="プロジェクト詳細を取得しました")


@router.get("/{project_id}/metrics")
def get_project_metrics(
    project: Project = Depends(deps.get_current_project),
    current_user: User = Depends(deps.get_current_active_user),
    formatter: ResponseFormatter = Depends(get_response_formatter),
    period: str = "month",  # week, month, quarter
) -> Dict[str, Any]:
    """
    プロジェクトのメトリクスを取得します

    権限チェック：プロジェクトメンバーのみアクセス可能

    Args:
        project: プロジェクト（権限チェック済み）
        current_user: 現在の認証済みユーザー
        period: 期間（week, month, quarter）

    Returns:
        プロジェクトメトリクス
    """
    try:
        logger.info(f"プロジェクトメトリクス取得: プロジェクトID {project.id}, 期間 {period}, ユーザー {current_user.email}")

        # サンプルメトリクスデータ
        metrics_data = {
            "throughput": {
                "completed_tasks": 45,
                "total_tasks": 60,
                "completion_rate": 75.0,
                "trend": "increasing",
            },
            "cycle_time": {
                "average_days": 3.2,
                "min_days": 1,
                "max_days": 8,
                "trend": "decreasing",
            },
            "lead_time": {
                "average_days": 5.8,
                "min_days": 2,
                "max_days": 12,
                "trend": "stable",
            },
            "bottlenecks": [
                {"stage": "コードレビュー", "avg_wait_time": 2.1, "frequency": 15},
                {"stage": "テスト", "avg_wait_time": 1.8, "frequency": 8},
            ],
            "team_velocity": {
                "current_sprint": 28,
                "previous_sprint": 25,
                "trend": "increasing",
            },
        }

        return formatter.success(
            data={
                "project_id": project.id,
                "period": period,
                "metrics": metrics_data,
                "cached": False,
            },
            message="プロジェクトメトリクスを取得しました",
        )

    except Exception as e:
        logger.error(f"プロジェクトメトリクス取得エラー: {e}")
        raise ExternalAPIException(service="メトリクスサービス", detail="プロジェクトメトリクスの取得に失敗しました")


@router.put("/{project_id}")
def update_project(
    update_data: ProjectUpdate,
    project: Project = Depends(deps.get_current_project_as_leader),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    プロジェクト情報を更新します

    権限チェック：プロジェクトリーダー以上の権限が必要

    Args:
        update_data: 更新データ
        project: プロジェクト（権限チェック済み）
        current_user: 現在の認証済みユーザー
        db: データベースセッション

    Returns:
        更新されたプロジェクト
    """
    logger.info(f"プロジェクト更新: プロジェクトID {project.id}, ユーザー {current_user.email}")

    # 更新データを適用
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    # Pydanticスキーマに変換
    project_data = ProjectSchema.model_validate(project).model_dump()

    return formatter.updated(data=project_data, message="プロジェクト情報を更新しました")


@router.delete("/{project_id}")
def delete_project(
    project: Project = Depends(deps.get_current_project_as_admin),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter),
) -> Dict[str, Any]:
    """
    プロジェクトを削除します

    権限チェック：管理者権限が必要

    Args:
        project: プロジェクト（権限チェック済み）
        current_user: 現在の認証済みユーザー
        db: データベースセッション

    Returns:
        削除結果
    """
    logger.info(f"プロジェクト削除: プロジェクトID {project.id}, ユーザー {current_user.email}")

    project_id = project.id
    db.delete(project)
    db.commit()

    return formatter.deleted(message=f"プロジェクト（ID: {project_id}）を削除しました")
