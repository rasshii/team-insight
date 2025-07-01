"""
統一的なエラーハンドリングミドルウェアとハンドラー
"""

from typing import Dict, Any, Union
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback

from app.core.exceptions import AppException, DatabaseException
from app.core.constants import ErrorCode

logger = logging.getLogger(__name__)


class ErrorResponse:
    """統一的なエラーレスポンス形式"""
    
    @staticmethod
    def create(
        error_code: str,
        message: str,
        status_code: int,
        details: Dict[str, Any] = None,
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        エラーレスポンスを作成
        
        Args:
            error_code: エラーコード
            message: エラーメッセージ
            status_code: HTTPステータスコード
            details: 追加の詳細情報
            request_id: リクエストID
            
        Returns:
            エラーレスポンスの辞書
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "status_code": status_code
        }
        
        if details:
            response["error"]["details"] = details
            
        if request_id:
            response["error"]["request_id"] = request_id
            
        return response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    カスタムAppExceptionのハンドラー
    
    Args:
        request: FastAPIのリクエストオブジェクト
        exc: AppException例外
        
    Returns:
        JSONレスポンス
    """
    request_id = request.headers.get("X-Request-ID")
    
    logger.error(
        f"AppException handled: {exc.error_code} - {exc.detail}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    response = ErrorResponse.create(
        error_code=exc.error_code,
        message=exc.detail,
        status_code=exc.status_code,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    通常のHTTPExceptionのハンドラー
    
    Args:
        request: FastAPIのリクエストオブジェクト
        exc: HTTPException
        
    Returns:
        JSONレスポンス
    """
    request_id = request.headers.get("X-Request-ID")
    
    # ステータスコードに基づいてエラーコードを決定
    error_code = ErrorCode.INTERNAL_ERROR.value
    if exc.status_code == status.HTTP_400_BAD_REQUEST:
        error_code = ErrorCode.DATA_VALIDATION_ERROR.value
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_code = ErrorCode.AUTH_INVALID_CREDENTIALS.value
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_code = ErrorCode.AUTH_PERMISSION_DENIED.value
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        error_code = ErrorCode.DATA_NOT_FOUND.value
    elif exc.status_code == status.HTTP_409_CONFLICT:
        error_code = ErrorCode.DATA_ALREADY_EXISTS.value
    
    logger.warning(
        f"HTTPException handled: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path
        }
    )
    
    response = ErrorResponse.create(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    バリデーションエラーのハンドラー
    
    Args:
        request: FastAPIのリクエストオブジェクト
        exc: RequestValidationError
        
    Returns:
        JSONレスポンス
    """
    request_id = request.headers.get("X-Request-ID")
    
    # エラーの詳細を整形
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error: {len(errors)} errors",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": errors
        }
    )
    
    response = ErrorResponse.create(
        error_code=ErrorCode.DATA_VALIDATION_ERROR.value,
        message="入力データの検証に失敗しました",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    データベース例外のハンドラー
    
    Args:
        request: FastAPIのリクエストオブジェクト
        exc: SQLAlchemyError
        
    Returns:
        JSONレスポンス
    """
    request_id = request.headers.get("X-Request-ID")
    
    logger.error(
        f"Database error: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_detail": str(exc)
        },
        exc_info=True
    )
    
    # 本番環境では詳細なエラー情報を隠す
    message = "データベースエラーが発生しました"
    if request.app.debug:
        message = f"データベースエラー: {str(exc)}"
    
    response = ErrorResponse.create(
        error_code=ErrorCode.DATABASE_ERROR.value,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    予期しない例外のハンドラー
    
    Args:
        request: FastAPIのリクエストオブジェクト
        exc: Exception
        
    Returns:
        JSONレスポンス
    """
    request_id = request.headers.get("X-Request-ID")
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_detail": str(exc),
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )
    
    # 本番環境では詳細なエラー情報を隠す
    message = "予期しないエラーが発生しました"
    details = None
    if request.app.debug:
        message = f"内部エラー: {str(exc)}"
        details = {
            "exception_type": type(exc).__name__,
            "exception_detail": str(exc)
        }
    
    response = ErrorResponse.create(
        error_code=ErrorCode.INTERNAL_ERROR.value,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response
    )


def register_error_handlers(app):
    """
    エラーハンドラーをアプリケーションに登録
    
    Args:
        app: FastAPIアプリケーションインスタンス
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    
    # 開発環境でのみ一般的な例外ハンドラーを登録
    if app.debug:
        app.add_exception_handler(Exception, general_exception_handler)