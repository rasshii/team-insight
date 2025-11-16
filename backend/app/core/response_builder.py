"""
統一的なAPIレスポンス形式を構築するユーティリティ
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone
from pydantic import BaseModel

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """レスポンスメタデータ"""

    timestamp: str
    version: str = "1.0"
    request_id: Optional[str] = None


class PaginationMeta(BaseModel):
    """ページネーションメタデータ"""

    total: int
    limit: int
    offset: int
    has_next: bool
    has_prev: bool
    current_page: int
    total_pages: int


class BaseResponse(BaseModel, Generic[T]):
    """基本レスポンス形式"""

    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    meta: ResponseMeta


class PaginatedResponse(BaseResponse[T]):
    """ページネーション付きレスポンス形式"""

    pagination: PaginationMeta


class ResponseBuilder:
    """レスポンス構築ヘルパークラス"""

    @staticmethod
    def success(data: Any = None, message: str = "処理が正常に完了しました", request_id: str = None) -> Dict[str, Any]:
        """
        成功レスポンスを構築

        Args:
            data: レスポンスデータ
            message: 成功メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        return {
            "success": True,
            "data": data,
            "message": message,
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0", "request_id": request_id},
        }

    @staticmethod
    def paginated(
        items: List[Any], total: int, limit: int, offset: int, message: str = "データを取得しました", request_id: str = None
    ) -> Dict[str, Any]:
        """
        ページネーション付きレスポンスを構築

        Args:
            items: アイテムリスト
            total: 総件数
            limit: 取得件数制限
            offset: オフセット
            message: メッセージ
            request_id: リクエストID

        Returns:
            ページネーション付きレスポンス辞書
        """
        current_page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "success": True,
            "data": items,
            "message": message,
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0", "request_id": request_id},
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
                "has_prev": offset > 0,
                "current_page": current_page,
                "total_pages": total_pages,
            },
        }

    @staticmethod
    def created(data: Any, message: str = "リソースが作成されました", request_id: str = None) -> Dict[str, Any]:
        """
        作成成功レスポンスを構築

        Args:
            data: 作成されたリソースデータ
            message: 成功メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        return ResponseBuilder.success(data=data, message=message, request_id=request_id)

    @staticmethod
    def updated(data: Any, message: str = "リソースが更新されました", request_id: str = None) -> Dict[str, Any]:
        """
        更新成功レスポンスを構築

        Args:
            data: 更新されたリソースデータ
            message: 成功メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        return ResponseBuilder.success(data=data, message=message, request_id=request_id)

    @staticmethod
    def deleted(message: str = "リソースが削除されました", request_id: str = None) -> Dict[str, Any]:
        """
        削除成功レスポンスを構築

        Args:
            message: 成功メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        return ResponseBuilder.success(data=None, message=message, request_id=request_id)

    @staticmethod
    def no_content(message: str = "データがありません", request_id: str = None) -> Dict[str, Any]:
        """
        コンテンツなしレスポンスを構築

        Args:
            message: メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        return ResponseBuilder.success(data=[], message=message, request_id=request_id)

    @staticmethod
    def accepted(task_id: str = None, message: str = "処理を受け付けました", request_id: str = None) -> Dict[str, Any]:
        """
        非同期処理受付レスポンスを構築

        Args:
            task_id: タスクID
            message: メッセージ
            request_id: リクエストID

        Returns:
            レスポンス辞書
        """
        data = {"task_id": task_id} if task_id else None
        return ResponseBuilder.success(data=data, message=message, request_id=request_id)


class ResponseFormatter:
    """レスポンスフォーマッター（依存性注入用）"""

    def __init__(self, request_id: str = None):
        self.request_id = request_id

    def success(self, data: Any = None, message: str = "処理が正常に完了しました") -> Dict[str, Any]:
        """成功レスポンスを構築"""
        return ResponseBuilder.success(data, message, self.request_id)

    def paginated(
        self, items: List[Any], total: int, limit: int, offset: int, message: str = "データを取得しました"
    ) -> Dict[str, Any]:
        """ページネーション付きレスポンスを構築"""
        return ResponseBuilder.paginated(items, total, limit, offset, message, self.request_id)

    def created(self, data: Any, message: str = "リソースが作成されました") -> Dict[str, Any]:
        """作成成功レスポンスを構築"""
        return ResponseBuilder.created(data, message, self.request_id)

    def updated(self, data: Any, message: str = "リソースが更新されました") -> Dict[str, Any]:
        """更新成功レスポンスを構築"""
        return ResponseBuilder.updated(data, message, self.request_id)

    def deleted(self, message: str = "リソースが削除されました") -> Dict[str, Any]:
        """削除成功レスポンスを構築"""
        return ResponseBuilder.deleted(message, self.request_id)

    def no_content(self, message: str = "データがありません") -> Dict[str, Any]:
        """コンテンツなしレスポンスを構築"""
        return ResponseBuilder.no_content(message, self.request_id)

    def accepted(self, task_id: str = None, message: str = "処理を受け付けました") -> Dict[str, Any]:
        """非同期処理受付レスポンスを構築"""
        return ResponseBuilder.accepted(task_id, message, self.request_id)
