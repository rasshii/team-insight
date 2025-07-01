"""
カスタム例外クラスとエラーハンドリング

統一されたエラーハンドリングのための例外クラスを提供します。
すべての例外は追加データフィールドをサポートし、
構造化されたエラーレスポンスを返します。
"""

from typing import Optional, Dict, Any, Union
from fastapi import HTTPException, status
from app.core.constants import ErrorCode, ErrorMessages
import logging

logger = logging.getLogger(__name__)


class AppException(HTTPException):
    """
    アプリケーション共通例外クラス
    
    すべてのカスタム例外の基底クラスです。
    エラーコード、追加データ、構造化ログをサポートします。
    """
    def __init__(
        self,
        error_code: Union[ErrorCode, str],
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code.value if isinstance(error_code, ErrorCode) else error_code
        self.data = data or {}
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        
        # 構造化ログ出力
        log_data = {
            "error_code": self.error_code,
            "status_code": status_code,
            "detail": detail,
            "data": self.data
        }
        logger.error("AppException raised", extra=log_data)


class AuthenticationException(AppException):
    """認証関連の例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.AUTHENTICATION_REQUIRED,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            data=data
        )


class TokenNotFoundException(AppException):
    """トークンが見つからない例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.TOKEN_NOT_FOUND,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            data=data
        )


class TokenExpiredException(AppException):
    """トークン期限切れ例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.TOKEN_EXPIRED,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            data=data
        )


class PermissionDeniedException(AppException):
    """権限不足例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.PERMISSION_DENIED,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.AUTH_PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            data=data
        )


class NotFoundException(AppException):
    """リソースが見つからない例外"""
    def __init__(
        self, 
        resource: str, 
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        if detail is None:
            detail = f"{resource}が見つかりません。"
        super().__init__(
            error_code=ErrorCode.DATA_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            data=data
        )


class AlreadyExistsException(AppException):
    """リソースがすでに存在する例外"""
    def __init__(
        self, 
        resource: str, 
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        if detail is None:
            detail = f"{resource}はすでに存在しています。"
        super().__init__(
            error_code=ErrorCode.DATA_ALREADY_EXISTS,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            data=data
        )


class ValidationException(AppException):
    """バリデーションエラー例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.INVALID_INPUT,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.DATA_VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            data=data
        )


class ExternalAPIException(AppException):
    """外部APIエラー例外"""
    def __init__(
        self, 
        service: str = "Backlog", 
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    ):
        if detail is None:
            detail = f"{service} APIの呼び出しに失敗しました。"
        super().__init__(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            status_code=status_code,
            detail=detail,
            data=data
        )


class DatabaseException(AppException):
    """データベースエラー例外"""
    def __init__(
        self, 
        detail: str = ErrorMessages.DATABASE_CONNECTION_ERROR,
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            data=data
        )


class RateLimitException(AppException):
    """レート制限エラー例外"""
    def __init__(
        self, 
        detail: str = "リクエスト数が制限を超えました",
        data: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        headers = None
        if retry_after:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers,
            data=data
        )


class BusinessLogicException(AppException):
    """ビジネスロジックエラー例外"""
    def __init__(
        self, 
        detail: str,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=status_code,
            detail=detail,
            data=data
        )


class AuthorizationException(AppException):
    """認可関連の例外（権限エラーとは異なる）"""
    def __init__(
        self, 
        detail: str = "このリソースへのアクセス権限がありません",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            data=data
        )


def handle_database_error(error: Exception) -> None:
    """
    データベースエラーをハンドリング
    
    Args:
        error: 発生した例外
        
    Raises:
        DatabaseException: データベースエラーとして再スロー
    """
    logger.error(f"Database error: {str(error)}", exc_info=True)
    raise DatabaseException()


def handle_external_api_error(service: str, error: Exception) -> None:
    """
    外部APIエラーをハンドリング
    
    Args:
        service: サービス名
        error: 発生した例外
        
    Raises:
        ExternalAPIException: 外部APIエラーとして再スロー
    """
    logger.error(f"{service} API error: {str(error)}", exc_info=True)
    raise ExternalAPIException(service=service)
