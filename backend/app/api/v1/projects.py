"""
プロジェクト管理API

このモジュールは、プロジェクト情報の取得と管理機能を提供します。
キャッシュ機能を活用して、データベースへの負荷を軽減します。
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.core.cache import cache_response, cache_invalidate
from app.core.security import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/")
@cache_response("projects_list", expire=600)  # 10分間キャッシュ
async def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクト一覧を取得します

    このエンドポイントは、ユーザーがアクセス可能なプロジェクト一覧を返します。
    結果は10分間キャッシュされ、データベースへの負荷を軽減します。

    Args:
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト一覧

    Raises:
        HTTPException: データ取得に失敗した場合
    """
    try:
        # 実際のデータベースクエリをシミュレート
        # 本番環境では実際のプロジェクトモデルを使用
        logger.info(f"プロジェクト一覧取得: ユーザー {current_user.email}")

        # データベースアクセスをシミュレート（重い処理）
        import asyncio
        await asyncio.sleep(0.5)  # 500msの遅延をシミュレート

        # サンプルデータ
        projects = [
            {
                "id": 1,
                "name": "Team Insight 開発",
                "description": "チームの生産性を可視化するWebアプリケーション",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-20T15:30:00Z"
            },
            {
                "id": 2,
                "name": "モバイルアプリ開発",
                "description": "iOS/Android向けのモバイルアプリケーション",
                "status": "planning",
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-18T14:20:00Z"
            },
            {
                "id": 3,
                "name": "データ分析基盤",
                "description": "ビッグデータ分析のための基盤システム",
                "status": "active",
                "created_at": "2024-01-05T11:00:00Z",
                "updated_at": "2024-01-19T16:45:00Z"
            }
        ]

        return {
            "message": "プロジェクト一覧を取得しました",
            "data": projects,
            "total": len(projects),
            "cached": True
        }

    except Exception as e:
        logger.error(f"プロジェクト一覧取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="プロジェクト一覧の取得に失敗しました"
        )

@router.get("/{project_id}")
@cache_response("project_detail", expire=300)  # 5分間キャッシュ
async def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクト詳細を取得します

    このエンドポイントは、指定されたプロジェクトの詳細情報を返します。
    結果は5分間キャッシュされ、データベースへの負荷を軽減します。

    Args:
        project_id: プロジェクトID
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクト詳細情報

    Raises:
        HTTPException: プロジェクトが見つからない、または取得に失敗した場合
    """
    try:
        logger.info(f"プロジェクト詳細取得: プロジェクトID {project_id}, ユーザー {current_user.email}")

        # データベースアクセスをシミュレート（重い処理）
        import asyncio
        await asyncio.sleep(0.3)  # 300msの遅延をシミュレート

        # サンプルデータ
        project_details = {
            1: {
                "id": 1,
                "name": "Team Insight 開発",
                "description": "チームの生産性を可視化するWebアプリケーション",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-20T15:30:00Z",
                "team_size": 8,
                "progress": 75,
                "technologies": ["Python", "FastAPI", "React", "PostgreSQL", "Redis"],
                "repository": "https://github.com/team/team-insight",
                "lead": {
                    "id": 1,
                    "name": "田中太郎",
                    "email": "tanaka@example.com"
                }
            },
            2: {
                "id": 2,
                "name": "モバイルアプリ開発",
                "description": "iOS/Android向けのモバイルアプリケーション",
                "status": "planning",
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-18T14:20:00Z",
                "team_size": 5,
                "progress": 20,
                "technologies": ["React Native", "TypeScript", "Firebase"],
                "repository": "https://github.com/team/mobile-app",
                "lead": {
                    "id": 2,
                    "name": "佐藤花子",
                    "email": "sato@example.com"
                }
            },
            3: {
                "id": 3,
                "name": "データ分析基盤",
                "description": "ビッグデータ分析のための基盤システム",
                "status": "active",
                "created_at": "2024-01-05T11:00:00Z",
                "updated_at": "2024-01-19T16:45:00Z",
                "team_size": 12,
                "progress": 60,
                "technologies": ["Python", "Apache Spark", "Kafka", "Elasticsearch"],
                "repository": "https://github.com/team/data-platform",
                "lead": {
                    "id": 3,
                    "name": "鈴木一郎",
                    "email": "suzuki@example.com"
                }
            }
        }

        if project_id not in project_details:
            raise HTTPException(
                status_code=404,
                detail=f"プロジェクトID {project_id} が見つかりません"
            )

        return {
            "message": "プロジェクト詳細を取得しました",
            "data": project_details[project_id],
            "cached": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"プロジェクト詳細取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="プロジェクト詳細の取得に失敗しました"
        )

@router.get("/{project_id}/metrics")
@cache_response("project_metrics", expire=180)  # 3分間キャッシュ
async def get_project_metrics(
    project_id: int,
    period: str = "month",  # week, month, quarter
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクトのメトリクスを取得します

    このエンドポイントは、プロジェクトの生産性メトリクスを返します。
    結果は3分間キャッシュされ、データベースへの負荷を軽減します。

    Args:
        project_id: プロジェクトID
        period: 期間（week, month, quarter）
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        プロジェクトメトリクス

    Raises:
        HTTPException: メトリクス取得に失敗した場合
    """
    try:
        logger.info(f"プロジェクトメトリクス取得: プロジェクトID {project_id}, 期間 {period}, ユーザー {current_user.email}")

        # データベースアクセスをシミュレート（重い処理）
        import asyncio
        await asyncio.sleep(0.8)  # 800msの遅延をシミュレート

        # サンプルメトリクスデータ
        metrics_data = {
            "throughput": {
                "completed_tasks": 45,
                "total_tasks": 60,
                "completion_rate": 75.0,
                "trend": "increasing"
            },
            "cycle_time": {
                "average_days": 3.2,
                "min_days": 1,
                "max_days": 8,
                "trend": "decreasing"
            },
            "lead_time": {
                "average_days": 5.8,
                "min_days": 2,
                "max_days": 12,
                "trend": "stable"
            },
            "bottlenecks": [
                {
                    "stage": "コードレビュー",
                    "avg_wait_time": 2.1,
                    "frequency": 15
                },
                {
                    "stage": "テスト",
                    "avg_wait_time": 1.8,
                    "frequency": 8
                }
            ],
            "team_velocity": {
                "current_sprint": 28,
                "previous_sprint": 25,
                "trend": "increasing"
            }
        }

        return {
            "message": "プロジェクトメトリクスを取得しました",
            "project_id": project_id,
            "period": period,
            "data": metrics_data,
            "cached": True
        }

    except Exception as e:
        logger.error(f"プロジェクトメトリクス取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="プロジェクトメトリクスの取得に失敗しました"
        )

@router.post("/{project_id}/refresh")
@cache_invalidate("project_*")  # プロジェクト関連のキャッシュを無効化
async def refresh_project_cache(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    プロジェクト関連のキャッシュを無効化します

    このエンドポイントは、プロジェクト関連のキャッシュを無効化し、
    次回のリクエストで最新のデータを取得できるようにします。

    Args:
        project_id: プロジェクトID
        db: データベースセッション
        current_user: 現在の認証済みユーザー

    Returns:
        キャッシュ無効化結果
    """
    try:
        logger.info(f"プロジェクトキャッシュ無効化: プロジェクトID {project_id}, ユーザー {current_user.email}")

        return {
            "message": f"プロジェクトID {project_id} のキャッシュを無効化しました",
            "project_id": project_id,
            "cache_invalidated": True
        }

    except Exception as e:
        logger.error(f"プロジェクトキャッシュ無効化エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail="キャッシュの無効化に失敗しました"
        )
