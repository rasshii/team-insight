"""
カスタム例外クラスとエラーハンドリング
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.constants import ErrorCode, ErrorMessages
import logging

logger = logging.getLogger(__name__)


class AppException(HTTPException):
    """
    アプリケーション共通例外クラス
    """
    def __init__(
        self,
        error_code: ErrorCode,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        logger.error(f"AppException: {error_code} - {detail}")


class AuthenticationException(AppException):
    """認証関連の例外"""
    def __init__(self, detail: str = ErrorMessages.AUTHENTICATION_REQUIRED):
        super().__init__(
            error_code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class TokenNotFoundException(AppException):
    """トークンが見つからない例外"""
    def __init__(self, detail: str = ErrorMessages.TOKEN_NOT_FOUND):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class TokenExpiredException(AppException):
    """トークン期限切れ例外"""
    def __init__(self, detail: str = ErrorMessages.TOKEN_EXPIRED):
        super().__init__(
            error_code=ErrorCode.AUTH_TOKEN_EXPIRED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class PermissionDeniedException(AppException):
    """権限不足例外"""
    def __init__(self, detail: str = ErrorMessages.PERMISSION_DENIED):
        super().__init__(
            error_code=ErrorCode.AUTH_PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(AppException):
    """リソースが見つからない例外"""
    def __init__(self, resource: str, detail: Optional[str] = None):
        if detail is None:
            detail = f"{resource}が見つかりません。"
        super().__init__(
            error_code=ErrorCode.DATA_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class AlreadyExistsException(AppException):
    """リソースがすでに存在する例外"""
    def __init__(self, resource: str, detail: Optional[str] = None):
        if detail is None:
            detail = f"{resource}はすでに存在しています。"
        super().__init__(
            error_code=ErrorCode.DATA_ALREADY_EXISTS,
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ValidationException(AppException):
    """バリデーションエラー例外"""
    def __init__(self, detail: str = ErrorMessages.INVALID_INPUT):
        super().__init__(
            error_code=ErrorCode.DATA_VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ExternalAPIException(AppException):
    """外部APIエラー例外"""
    def __init__(self, service: str = "Backlog", detail: Optional[str] = None):
        if detail is None:
            detail = f"{service} APIの呼び出しに失敗しました。"
        super().__init__(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class DatabaseException(AppException):
    """データベースエラー例外"""
    def __init__(self, detail: str = ErrorMessages.DATABASE_CONNECTION_ERROR):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
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
