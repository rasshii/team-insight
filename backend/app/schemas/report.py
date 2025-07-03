"""
レポート配信関連のPydanticスキーマ

このモジュールは、レポート配信機能で使用される
リクエスト/レスポンスのスキーマを定義します。
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReportType(str, Enum):
    """レポートタイプ"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportRecipientType(str, Enum):
    """レポート受信者タイプ"""
    PERSONAL = "personal"
    PROJECT = "project"
    TEAM = "team"


class ReportScheduleRequest(BaseModel):
    """
    レポート配信スケジュール設定リクエスト
    """
    report_type: ReportType = Field(..., description="レポートタイプ")
    recipient_type: ReportRecipientType = Field(..., description="受信者タイプ")
    project_id: Optional[int] = Field(None, description="プロジェクトID（PROJECT受信者タイプの場合必須）")
    enabled: bool = Field(default=True, description="配信有効/無効")
    send_time: Optional[str] = Field(None, description="送信時刻（HH:MM形式）", pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "weekly",
                "recipient_type": "personal",
                "enabled": True,
                "send_time": "09:00"
            }
        }


class ReportScheduleResponse(BaseModel):
    """
    レポート配信スケジュール設定レスポンス
    """
    id: int = Field(..., description="スケジュールID")
    user_id: int = Field(..., description="ユーザーID")
    report_type: ReportType = Field(..., description="レポートタイプ")
    recipient_type: ReportRecipientType = Field(..., description="受信者タイプ")
    project_id: Optional[int] = Field(None, description="プロジェクトID")
    enabled: bool = Field(..., description="配信有効/無効")
    send_time: Optional[str] = Field(None, description="送信時刻")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    
    class Config:
        from_attributes = True


class TestReportRequest(BaseModel):
    """
    テストレポート送信リクエスト
    """
    report_type: ReportType = Field(..., description="レポートタイプ")
    recipient_type: ReportRecipientType = Field(..., description="受信者タイプ")
    project_id: Optional[int] = Field(None, description="プロジェクトID（PROJECT受信者タイプの場合必須）")
    email: Optional[str] = Field(None, description="送信先メールアドレス（指定しない場合は登録メールアドレス）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "weekly",
                "recipient_type": "personal"
            }
        }


class ReportDeliveryHistoryResponse(BaseModel):
    """
    レポート配信履歴レスポンス
    """
    id: int = Field(..., description="履歴ID")
    user_id: int = Field(..., description="ユーザーID")
    report_type: ReportType = Field(..., description="レポートタイプ")
    recipient_type: ReportRecipientType = Field(..., description="受信者タイプ")
    project_id: Optional[int] = Field(None, description="プロジェクトID")
    email: str = Field(..., description="送信先メールアドレス")
    status: str = Field(..., description="送信ステータス（success/failed）")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    sent_at: datetime = Field(..., description="送信日時")
    
    class Config:
        from_attributes = True


class ReportScheduleListResponse(BaseModel):
    """
    レポート配信スケジュール一覧レスポンス
    """
    schedules: List[ReportScheduleResponse] = Field(..., description="スケジュール一覧")
    total: int = Field(..., description="総件数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schedules": [
                    {
                        "id": 1,
                        "user_id": 1,
                        "report_type": "weekly",
                        "recipient_type": "personal",
                        "enabled": True,
                        "send_time": "09:00",
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": "2025-01-01T00:00:00"
                    }
                ],
                "total": 1
            }
        }