"""
リクエストIDミドルウェア
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    リクエストIDを生成・管理するミドルウェア
    
    各リクエストに一意のIDを付与し、レスポンスヘッダーに含める
    """
    
    async def dispatch(self, request: Request, call_next):
        # リクエストヘッダーからリクエストIDを取得、なければ生成
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # リクエストのstateにリクエストIDを保存
        request.state.request_id = request_id
        
        # 次のミドルウェア/エンドポイントを実行
        response = await call_next(request)
        
        # レスポンスヘッダーにリクエストIDを追加
        response.headers["X-Request-ID"] = request_id
        
        return response