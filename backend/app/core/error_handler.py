"""
統一的なエラーハンドリングミドルウェアとハンドラー

このモジュールは、FastAPIアプリケーションの統一的なエラーハンドリング機能を提供します。
全ての例外を適切にキャッチし、一貫性のあるエラーレスポンスを返します。

主要な機能:
    1. 統一的なエラーレスポンス形式
       - エラーコード
       - エラーメッセージ
       - タイムスタンプ
       - リクエストID（トレーシング用）

    2. 例外の種類に応じたハンドリング
       - カスタム例外（AppException）
       - HTTP例外（HTTPException）
       - バリデーションエラー（RequestValidationError）
       - データベースエラー（SQLAlchemyError）
       - 予期しない例外（Exception）

    3. 開発環境と本番環境の分離
       - 開発環境: 詳細なエラー情報を返す
       - 本番環境: セキュリティのため簡潔なメッセージのみ

主要なクラス・関数:
    - ErrorResponse: 統一的なエラーレスポンス生成クラス
    - app_exception_handler(): カスタム例外ハンドラー
    - http_exception_handler(): HTTP例外ハンドラー
    - validation_exception_handler(): バリデーションエラーハンドラー
    - database_exception_handler(): データベース例外ハンドラー
    - general_exception_handler(): 一般例外ハンドラー
    - register_error_handlers(): エラーハンドラーの一括登録

エラーレスポンスの形式:
    ```json
    {
        "error": {
            "code": "DATA_NOT_FOUND",
            "message": "指定されたデータが見つかりません",
            "timestamp": "2025-01-15T12:34:56.789Z",
            "request_id": "abc123",
            "details": {
                "validation_errors": [...]  // オプション
            }
        },
        "status_code": 404
    }
    ```

使用例:
    ```python
    from app.core.error_handler import register_error_handlers

    # FastAPIアプリケーション初期化時
    app = FastAPI()
    register_error_handlers(app)

    # カスタム例外の使用
    from app.core.exceptions import AppException
    from app.core.constants import ErrorCode

    raise AppException(
        status_code=404,
        error_code=ErrorCode.DATA_NOT_FOUND,
        detail="ユーザーが見つかりません"
    )
    ```

エラーハンドリングの流れ:
    1. 例外が発生
    2. FastAPIが例外をキャッチ
    3. 登録されたハンドラーが呼び出される
    4. 統一形式のエラーレスポンスを生成
    5. ログに記録
    6. クライアントにレスポンスを返す

セキュリティの考慮事項:
    - 本番環境では詳細なエラー情報を隠す
    - スタックトレースは開発環境のみ
    - SQLエラーの詳細は公開しない
    - 攻撃者に有用な情報を与えない

ロギング:
    - 全てのエラーをログに記録
    - リクエストIDでトレーシング可能
    - エラーレベルに応じてログレベルを調整
"""

from typing import Dict, Any, Union, Optional, List
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
import logging
import traceback

from app.core.exceptions import AppException, DatabaseException
from app.core.constants import ErrorCode

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """エラーの詳細情報"""

    field: Optional[str] = Field(None, description="エラーが発生したフィールド名")
    reason: Optional[str] = Field(None, description="エラーの理由")
    value: Optional[Any] = Field(None, description="問題のある値")


class ErrorResponse:
    """統一的なエラーレスポンス形式とテンプレート"""

    @staticmethod
    def create(
        error_code: str,
        message: str,
        status_code: int,
        details: Union[Dict[str, Any], List[ErrorDetail]] = None,
        request_id: str = None,
    ) -> Dict[str, Any]:
        """
        エラーレスポンスを作成

        Args:
            error_code: エラーコード
            message: エラーメッセージ
            status_code: HTTPステータスコード
            details: 追加の詳細情報（辞書またはErrorDetailのリスト）
            request_id: リクエストID

        Returns:
            エラーレスポンスの辞書
        """
        response = {
            "error": {"code": error_code, "message": message, "timestamp": datetime.now(timezone.utc).isoformat()},
            "status_code": status_code,
        }

        if details:
            if isinstance(details, list) and all(isinstance(d, ErrorDetail) for d in details):
                response["error"]["details"] = [d.model_dump() for d in details]
            else:
                response["error"]["details"] = details

        if request_id:
            response["error"]["request_id"] = request_id

        return response

    @staticmethod
    def unauthorized(
        message: str = "認証が必要です", details: Optional[List[ErrorDetail]] = None, request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """401 Unauthorizedエラー"""
        return ErrorResponse.create(
            error_code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def forbidden(
        message: str = "アクセス権限がありません", details: Optional[List[ErrorDetail]] = None, request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """403 Forbiddenエラー"""
        return ErrorResponse.create(
            error_code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def not_found(
        resource: str,
        identifier: Union[str, int],
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """404 Not Foundエラー"""
        return ErrorResponse.create(
            error_code="NOT_FOUND",
            message=f"{resource}（ID: {identifier}）が見つかりません",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def validation_error(
        message: str = "入力値が無効です", errors: List[Dict[str, Any]] = None, request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """422 Validation Errorエラー"""
        details = []
        if errors:
            for error in errors:
                details.append(
                    ErrorDetail(
                        field=".".join(str(loc) for loc in error.get("loc", [])),
                        reason=error.get("msg", ""),
                        value=error.get("input"),
                    )
                )

        return ErrorResponse.create(
            error_code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details if details else None,
            request_id=request_id,
        )

    @staticmethod
    def conflict(
        message: str,
        resource: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """409 Conflictエラー"""
        return ErrorResponse.create(
            error_code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def internal_server_error(
        message: str = "内部サーバーエラーが発生しました",
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """500 Internal Server Errorエラー"""
        return ErrorResponse.create(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def bad_gateway(
        service: str,
        message: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """502 Bad Gatewayエラー"""
        default_message = f"{service}への接続に失敗しました"
        return ErrorResponse.create(
            error_code="BAD_GATEWAY",
            message=message or default_message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            request_id=request_id,
        )

    @staticmethod
    def service_unavailable(
        message: str = "サービスが一時的に利用できません",
        retry_after: Optional[int] = None,
        details: Optional[List[ErrorDetail]] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """503 Service Unavailableエラー"""
        error_response = ErrorResponse.create(
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            request_id=request_id,
        )

        if retry_after:
            error_response["error"]["retry_after"] = retry_after

        return error_response


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
            "path": request.url.path,
        },
    )

    response = ErrorResponse.create(
        error_code=exc.error_code, message=exc.detail, status_code=exc.status_code, request_id=request_id
    )

    return JSONResponse(status_code=exc.status_code, content=response)


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
        extra={"status_code": exc.status_code, "request_id": request_id, "path": request.url.path},
    )

    response = ErrorResponse.create(
        error_code=error_code, message=str(exc.detail), status_code=exc.status_code, request_id=request_id
    )

    return JSONResponse(status_code=exc.status_code, content=response)


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
        errors.append({"field": ".".join(str(loc) for loc in error["loc"]), "message": error["msg"], "type": error["type"]})

    logger.warning(
        f"Validation error: {len(errors)} errors", extra={"request_id": request_id, "path": request.url.path, "errors": errors}
    )

    response = ErrorResponse.create(
        error_code=ErrorCode.DATA_VALIDATION_ERROR.value,
        message="入力データの検証に失敗しました",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
        request_id=request_id,
    )

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response)


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
        extra={"request_id": request_id, "path": request.url.path, "error_detail": str(exc)},
        exc_info=True,
    )

    # 本番環境では詳細なエラー情報を隠す
    message = "データベースエラーが発生しました"
    if request.app.debug:
        message = f"データベースエラー: {str(exc)}"

    response = ErrorResponse.create(
        error_code=ErrorCode.DATABASE_ERROR.value,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)


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
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    # 本番環境では詳細なエラー情報を隠す
    message = "予期しないエラーが発生しました"
    details = None
    if request.app.debug:
        message = f"内部エラー: {str(exc)}"
        details = {"exception_type": type(exc).__name__, "exception_detail": str(exc)}

    response = ErrorResponse.create(
        error_code=ErrorCode.INTERNAL_ERROR.value,
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
        request_id=request_id,
    )

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)


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
