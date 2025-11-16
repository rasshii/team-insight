"""
レスポンスフォーマッター

API レスポンスの形式を統一するためのフォーマッター
"""

from typing import Any, Callable, Dict
from fastapi import Request


class ResponseFormatter:
    """レスポンスフォーマッタークラス"""

    def __init__(self, request: Request):
        self.request = request

    def __call__(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """レスポンスをフォーマット"""
        # リクエストIDがあれば追加
        if hasattr(self.request.state, "request_id"):
            response["request_id"] = self.request.state.request_id

        return response


def get_response_formatter(request: Request) -> ResponseFormatter:
    """レスポンスフォーマッターを取得"""
    return ResponseFormatter(request)
