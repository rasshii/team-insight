"""
API レスポンスの統一的なスキーマ定義

このモジュールは、API全体で使用される統一的なレスポンス
フォーマットのPydanticスキーマを定義します。
"""

from typing import TypeVar, Generic, Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


# 汎用的な型変数
DataT = TypeVar('DataT')


class SuccessResponse(GenericModel, Generic[DataT]):
    """成功レスポンスの基本スキーマ"""
    
    success: bool = Field(True, description="成功フラグ")
    data: DataT = Field(..., description="レスポンスデータ")
    message: Optional[str] = Field(None, description="成功メッセージ")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="レスポンス生成時刻"
    )


class ErrorDetail(BaseModel):
    """エラーの詳細情報"""
    field: Optional[str] = Field(None, description="エラーが発生したフィールド")
    reason: str = Field(..., description="エラーの理由")
    value: Optional[Any] = Field(None, description="問題のある値")


class ErrorResponse(BaseModel):
    """エラーレスポンスのスキーマ"""
    
    error: dict = Field(..., description="エラー情報")
    status_code: int = Field(..., description="HTTPステータスコード")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "入力値が無効です",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "details": [
                        {
                            "field": "email",
                            "reason": "有効なメールアドレスではありません",
                            "value": "invalid-email"
                        }
                    ]
                },
                "status_code": 422
            }
        }


class PaginationMeta(BaseModel):
    """ページネーション情報"""
    total: int = Field(..., ge=0, description="総件数")
    page: int = Field(..., ge=1, description="現在のページ番号")
    per_page: int = Field(..., ge=1, le=100, description="1ページあたりの件数")
    total_pages: int = Field(..., ge=0, description="総ページ数")
    has_next: bool = Field(..., description="次ページの有無")
    has_prev: bool = Field(..., description="前ページの有無")


class PaginatedResponse(GenericModel, Generic[DataT]):
    """ページネーション付きレスポンス"""
    
    success: bool = Field(True, description="成功フラグ")
    data: List[DataT] = Field(..., description="データリスト")
    meta: PaginationMeta = Field(..., description="ページネーション情報")
    message: Optional[str] = Field(None, description="メッセージ")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="レスポンス生成時刻"
    )


class BulkOperationResult(BaseModel):
    """一括操作の結果"""
    
    succeeded: int = Field(0, ge=0, description="成功件数")
    failed: int = Field(0, ge=0, description="失敗件数")
    errors: List[ErrorDetail] = Field(
        default_factory=list,
        description="エラー詳細リスト"
    )


class BulkOperationResponse(BaseModel):
    """一括操作レスポンス"""
    
    success: bool = Field(..., description="全体の成功フラグ")
    result: BulkOperationResult = Field(..., description="操作結果")
    message: str = Field(..., description="結果メッセージ")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="レスポンス生成時刻"
    )


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    
    status: str = Field(..., description="サービスステータス")
    timestamp: str = Field(..., description="チェック時刻")
    version: Optional[str] = Field(None, description="APIバージョン")
    services: Optional[dict] = Field(None, description="依存サービスの状態")


class MessageResponse(BaseModel):
    """シンプルなメッセージレスポンス"""
    
    success: bool = Field(..., description="成功フラグ")
    message: str = Field(..., description="メッセージ")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="レスポンス生成時刻"
    )


class StatusResponse(BaseModel):
    """ステータス確認レスポンス"""
    
    status: str = Field(..., description="ステータス")
    details: Optional[dict] = Field(None, description="詳細情報")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="レスポンス生成時刻"
    )


# 便利な型エイリアス
StringListResponse = SuccessResponse[List[str]]
DictResponse = SuccessResponse[dict]