"""
共通の依存性注入
"""

from typing import Optional
from fastapi import Depends, Request
from app.core.response_builder import ResponseFormatter


def get_request_id(request: Request) -> Optional[str]:
    """
    リクエストIDを取得

    Args:
        request: FastAPIのリクエストオブジェクト

    Returns:
        リクエストID（存在しない場合はNone）
    """
    return getattr(request.state, "request_id", None)


def get_response_formatter(request_id: Optional[str] = Depends(get_request_id)) -> ResponseFormatter:
    """
    ResponseFormatterインスタンスを取得

    Args:
        request_id: リクエストID

    Returns:
        ResponseFormatterインスタンス
    """
    return ResponseFormatter(request_id=request_id)
