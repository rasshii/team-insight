"""
プロジェクト管理API

このモジュールは、プロジェクト情報の取得と管理機能を提供します。
キャッシュ機能を活用して、データベースへの負荷を軽減します。
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.api import deps
from datetime import timedelta
from app.models.project import Project
from app.schemas.project import Project as ProjectSchema, ProjectUpdate
from app.db.session import get_db
from app.core.cache import cache_response, cache_invalidate
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[ProjectSchema])
def get_projects(
    db: Session = Depends(deps.get_db_session), 
    current_user: User = Depends(deps.get_current_active_user)
) -> List[Project]:
    """
    現在のユーザーが参加しているプロジェクト一覧を取得
    
    Args:
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト一覧
    """
    # ユーザーが参加しているプロジェクトを取得（リレーションシップを含む）
    user_with_projects = db.query(User).options(joinedload(User.projects)).filter(User.id == current_user.id).first()
    return user_with_projects.projects if user_with_projects else []


@router.get("/{project_id}", response_model=ProjectSchema)
def get_project_detail(
    project: Project = Depends(deps.get_current_project),
    current_user: User = Depends(deps.get_current_active_user)
) -> Project:
    """
    プロジェクト詳細を取得します

    権限チェック：プロジェクトメンバーのみアクセス可能

    Args:
        project: プロジェクト（権限チェック済み）
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト詳細情報
    """
    logger.info(
        f"プロジェクト詳細取得: プロジェクトID {project.id}, ユーザー {current_user.email}"
    )
    return project


@router.get("/{project_id}/metrics")
def get_project_metrics(
    project: Project = Depends(deps.get_current_project),
    current_user: User = Depends(deps.get_current_active_user),
    period: str = "month"  # week, month, quarter
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
        logger.info(
            f"プロジェクトメトリクス取得: プロジェクトID {project.id}, 期間 {period}, ユーザー {current_user.email}"
        )

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

        return {
            "message": "プロジェクトメトリクスを取得しました",
            "project_id": project.id,
            "period": period,
            "data": metrics_data,
            "cached": False,
        }

    except Exception as e:
        logger.error(f"プロジェクトメトリクス取得エラー: {e}")
        raise HTTPException(
            status_code=500, detail="プロジェクトメトリクスの取得に失敗しました"
        )


@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    update_data: ProjectUpdate,
    project: Project = Depends(deps.get_current_project_as_leader),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session)
) -> Project:
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
    logger.info(
        f"プロジェクト更新: プロジェクトID {project.id}, ユーザー {current_user.email}"
    )
    
    # 更新データを適用
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project: Project = Depends(deps.get_current_project_as_admin),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db_session)
) -> Dict[str, str]:
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
    logger.info(
        f"プロジェクト削除: プロジェクトID {project.id}, ユーザー {current_user.email}"
    )
    
    db.delete(project)
    db.commit()
    
    return {"message": f"プロジェクト（ID: {project.id}）を削除しました"}
