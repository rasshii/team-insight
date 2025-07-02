"""
統一的なエラーレスポンスビルダー

このモジュールは、API全体で一貫したエラーレスポンス形式を
提供するためのビルダークラスとヘルパー関数を定義します。
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import status


class ErrorDetail(BaseModel):
    """エラーの詳細情報"""
    field: Optional[str] = Field(None, description="エラーが発生したフィールド名")
    reason: Optional[str] = Field(None, description="エラーの理由")
    value: Optional[Any] = Field(None, description="問題のある値")


class ErrorInfo(BaseModel):
    """エラー情報の構造"""
    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    timestamp: str = Field(..., description="エラー発生時刻")
    details: Optional[List[ErrorDetail]] = Field(None, description="詳細情報")
    request_id: Optional[str] = Field(None, description="リクエストID")
    trace_id: Optional[str] = Field(None, description="トレースID")


class ErrorResponseModel(BaseModel):
    """エラーレスポンスのモデル"""
    error: ErrorInfo
    status_code: int


class StandardErrorResponses:
    """標準的なエラーレスポンスのテンプレート"""
    
    @staticmethod
    def unauthorized(
        message: str = "認証が必要です",
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """401 Unauthorizedエラー"""
        return {
            "error": {
                "code": "UNAUTHORIZED",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_401_UNAUTHORIZED
        }
    
    @staticmethod
    def forbidden(
        message: str = "アクセス権限がありません",
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """403 Forbiddenエラー"""
        return {
            "error": {
                "code": "FORBIDDEN",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_403_FORBIDDEN
        }
    
    @staticmethod
    def not_found(
        resource: str,
        identifier: Union[str, int],
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """404 Not Foundエラー"""
        return {
            "error": {
                "code": "NOT_FOUND",
                "message": f"{resource}（ID: {identifier}）が見つかりません",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_404_NOT_FOUND
        }
    
    @staticmethod
    def validation_error(
        message: str = "入力値が無効です",
        errors: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """422 Validation Errorエラー"""
        details = []
        if errors:
            for error in errors:
                details.append(ErrorDetail(
                    field=".".join(str(loc) for loc in error.get("loc", [])),
                    reason=error.get("msg", ""),
                    value=error.get("input")
                ))
        
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        }
    
    @staticmethod
    def conflict(
        message: str,
        resource: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """409 Conflictエラー"""
        return {
            "error": {
                "code": "CONFLICT",
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_409_CONFLICT
        }
    
    @staticmethod
    def internal_server_error(
        message: str = "内部サーバーエラーが発生しました",
        request_id: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """500 Internal Server Errorエラー"""
        error_info = {
            "code": "INTERNAL_SERVER_ERROR",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": [d.model_dump() for d in details] if details else None
        }
        
        if request_id:
            error_info["request_id"] = request_id
        
        return {
            "error": error_info,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    
    @staticmethod
    def bad_gateway(
        service: str,
        message: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """502 Bad Gatewayエラー"""
        default_message = f"{service}への接続に失敗しました"
        return {
            "error": {
                "code": "BAD_GATEWAY",
                "message": message or default_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": [d.model_dump() for d in details] if details else None
            },
            "status_code": status.HTTP_502_BAD_GATEWAY
        }
    
    @staticmethod
    def service_unavailable(
        message: str = "サービスが一時的に利用できません",
        retry_after: Optional[int] = None,
        details: Optional[List[ErrorDetail]] = None
    ) -> Dict[str, Any]:
        """503 Service Unavailableエラー"""
        error_info = {
            "code": "SERVICE_UNAVAILABLE",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": [d.model_dump() for d in details] if details else None
        }
        
        if retry_after:
            error_info["retry_after"] = retry_after
        
        return {
            "error": error_info,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE
        }