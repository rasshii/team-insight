"""
ヘルスチェック関連のスキーマ定義

このモジュールは、ヘルスチェックAPIのリクエスト/レスポンススキーマを定義します。
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class ServiceStatus(BaseModel):
    """各サービスの健全性ステータス"""

    api: Literal["healthy", "unhealthy"] = Field(..., description="APIサーバーの状態")
    database: Literal["healthy", "unhealthy"] = Field(..., description="データベースの状態")
    redis: Literal["healthy", "unhealthy"] = Field(..., description="Redisキャッシュの状態")


class HealthResponse(BaseModel):
    """ヘルスチェックのレスポンス"""

    status: Literal["healthy", "unhealthy"] = Field(..., description="システム全体の健全性ステータス")
    services: ServiceStatus = Field(..., description="各サービスの健全性ステータス")
    message: str = Field(..., description="ステータスメッセージ", example="Team Insight API is running")
    timestamp: datetime = Field(..., description="チェック実行時刻")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "services": {"api": "healthy", "database": "healthy", "redis": "healthy"},
                "message": "Team Insight API is running",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        }
