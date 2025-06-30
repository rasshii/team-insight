from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode

from app.api.deps import get_db_session
from app.models.user import User
from app.models.auth import OAuthToken
from app.core.security import get_current_user
from app.core.response_builder import ResponseBuilder, ResponseFormatter
from app.core.deps import get_response_formatter
from app.core.error_handler import AppException, ErrorCode
from app.schemas.backlog import (
    BacklogApiKeyConnect,
    BacklogOAuthConnect,
    BacklogConnectionStatus,
    BacklogConnectionTest,
    BacklogDisconnect
)
from app.core.config import settings


router = APIRouter()


@router.get("/connection", response_model=BacklogConnectionStatus)
async def get_connection_status(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> BacklogConnectionStatus:
    """
    Backlog連携状態を取得する
    """
    # OAuthトークンを取得
    oauth_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not oauth_token:
        response_data = BacklogConnectionStatus(
            is_connected=False,
            space_key=None,
            connection_type=None,
            connected_at=None,
            last_sync_at=None,
            expires_at=None,
            user_email=None
        )
        return response_data
    
    # トークンの有効性をチェック
    is_expired = oauth_token.expires_at and oauth_token.expires_at < datetime.utcnow()
    
    response_data = BacklogConnectionStatus(
        is_connected=not is_expired,
        space_key=oauth_token.backlog_space_key,
        connection_type="api_key" if oauth_token.is_api_key else "oauth",
        connected_at=oauth_token.created_at,
        last_sync_at=oauth_token.last_used_at,
        expires_at=oauth_token.expires_at,
        user_email=oauth_token.backlog_user_email
    )
    
    return response_data


@router.post("/connect/api-key")
async def connect_with_api_key(
    connection_data: BacklogApiKeyConnect,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    APIキーでBacklogと連携する
    """
    # APIキーの有効性をテスト
    test_url = f"https://{connection_data.space_key}.backlog.jp/api/v2/users/myself"
    headers = {"apiKey": connection_data.api_key}
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        user_info = response.json()
    except requests.exceptions.RequestException as e:
        raise AppException(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            detail="APIキーが無効か、スペースキーが正しくありません",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # 既存のトークンを削除
    db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).delete()
    
    # 新しいトークンを作成
    oauth_token = OAuthToken(
        user_id=current_user.id,
        provider="backlog",
        access_token=connection_data.api_key,
        refresh_token=None,
        expires_at=None,  # APIキーは無期限
        is_api_key=True,
        backlog_space_key=connection_data.space_key,
        backlog_user_id=str(user_info.get("id")),
        backlog_user_email=user_info.get("mailAddress")
    )
    
    db.add(oauth_token)
    db.commit()
    
    return formatter(ResponseBuilder.success(
        data={
            "is_connected": True,
            "space_key": connection_data.space_key,
            "connection_type": "api_key",
            "user_email": user_info.get("mailAddress")
        },
        message="Backlog連携が完了しました"
    ))


@router.post("/connect/oauth")
async def connect_with_oauth(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    OAuthでBacklogと連携を開始する（認証URLを返す）
    """
    # OAuth認証URLを生成
    params = {
        "response_type": "code",
        "client_id": settings.BACKLOG_CLIENT_ID,
        "redirect_uri": settings.BACKLOG_REDIRECT_URI,
        "state": f"user_{current_user.id}"  # ユーザーIDを状態に含める
    }
    
    auth_url = f"https://{settings.BACKLOG_SPACE_KEY}.backlog.jp/OAuth2/authorize?{urlencode(params)}"
    
    return formatter(ResponseBuilder.success(
        data={"auth_url": auth_url},
        message="Backlog認証ページへリダイレクトしてください"
    ))


@router.post("/test")
async def test_connection(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    Backlog接続をテストする
    """
    # OAuthトークンを取得
    oauth_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not oauth_token:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            detail="Backlog連携が設定されていません",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # APIリクエストを送信
    url = f"https://{oauth_token.backlog_space_key}.backlog.jp/api/v2/users/myself"
    
    if oauth_token.is_api_key:
        headers = {"apiKey": oauth_token.access_token}
    else:
        headers = {"Authorization": f"Bearer {oauth_token.access_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        user_info = response.json()
        
        # 最終使用日時を更新
        oauth_token.last_used_at = datetime.utcnow()
        db.commit()
        
        return formatter(ResponseBuilder.success(
            data={
                "success": True,
                "message": "接続テストに成功しました",
                "user_info": {
                    "id": user_info.get("id"),
                    "name": user_info.get("name"),
                    "email": user_info.get("mailAddress")
                }
            }
        ))
    except requests.exceptions.RequestException as e:
        error_message = "接続テストに失敗しました"
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                error_message = "認証エラー: トークンが無効です"
            elif e.response.status_code == 404:
                error_message = "スペースが見つかりません"
        
        return formatter(ResponseBuilder.success(
            data={
                "success": False,
                "message": error_message,
                "user_info": None
            }
        ))


@router.post("/disconnect")
async def disconnect_backlog(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    Backlog連携を解除する
    """
    # OAuthトークンを削除
    deleted = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).delete()
    
    if deleted == 0:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            detail="Backlog連携が見つかりません",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    db.commit()
    
    return formatter(ResponseBuilder.success(
        data={
            "success": True,
            "message": "Backlog連携を解除しました"
        }
    ))