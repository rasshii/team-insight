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
    BacklogOAuthConnect,
    BacklogConnectionStatus,
    BacklogConnectionTest,
    BacklogDisconnect,
    BacklogSpaceKeyUpdate
)
from app.core.config import settings
from app.services.backlog_client import backlog_client
from app.core.cache import cache_response, cache_invalidate
from app.core.redis_client import redis_client
import json
import logging

logger = logging.getLogger(__name__)

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
    
    # space_keyはOAuthTokenから取得、なければ設定から取得
    from app.core.config import settings
    
    space_key = oauth_token.backlog_space_key
    if not space_key and hasattr(settings, 'BACKLOG_SPACE_KEY'):
        space_key = settings.BACKLOG_SPACE_KEY
    
    response_data = BacklogConnectionStatus(
        is_connected=not is_expired,
        space_key=space_key,
        connection_type="oauth",
        connected_at=oauth_token.created_at,
        last_sync_at=oauth_token.last_used_at if oauth_token.last_used_at else oauth_token.updated_at,
        expires_at=oauth_token.expires_at,
        user_email=oauth_token.backlog_user_email if oauth_token.backlog_user_email else current_user.email
    )
    
    return response_data



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
    
    return formatter.success(
        data={"auth_url": auth_url},
        message="Backlog認証ページへリダイレクトしてください"
    )


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
    headers = {"Authorization": f"Bearer {oauth_token.access_token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        user_info = response.json()
        
        # 最終使用日時を更新
        oauth_token.last_used_at = datetime.utcnow()
        db.commit()
        
        return formatter.success(
            data={
                "success": True,
                "message": "接続テストに成功しました",
                "user_info": {
                    "id": user_info.get("id"),
                    "name": user_info.get("name"),
                    "email": user_info.get("mailAddress")
                }
            }
        )
    except requests.exceptions.RequestException as e:
        error_message = "接続テストに失敗しました"
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                error_message = "認証エラー: トークンが無効です"
            elif e.response.status_code == 404:
                error_message = "スペースが見つかりません"
        
        return formatter.success(
            data={
                "success": False,
                "message": error_message,
                "user_info": None
            }
        )


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
    
    return formatter.success(
        data={
            "success": True,
            "message": "Backlog連携を解除しました"
        }
    )


@router.put("/connection/space-key")
async def update_space_key(
    request: BacklogSpaceKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    Backlogスペースキーを更新する
    
    既存のOAuthトークンに紐づくスペースキーを更新します。
    """
    # OAuthトークンの存在確認
    oauth_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "backlog"
    ).first()
    
    if not oauth_token:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            detail="Backlog連携が見つかりません。先に連携を行ってください。",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # スペースキーを更新
    oauth_token.backlog_space_key = request.space_key
    oauth_token.updated_at = datetime.utcnow()
    oauth_token.last_used_at = datetime.utcnow()
    
    db.commit()
    
    return formatter.success(
        data={
            "success": True,
            "message": f"スペースキーを '{request.space_key}' に更新しました",
            "space_key": request.space_key
        }
    )


@router.get("/projects/{project_id}/statuses")
async def get_project_statuses(
    project_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    プロジェクトのステータス一覧を取得する
    
    Backlog APIからプロジェクト固有のステータス一覧を取得します。
    結果は5分間キャッシュされます。
    """
    # プロジェクトを取得してBacklog IDを確認
    from app.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise AppException(
            error_code=ErrorCode.NOT_FOUND,
            detail="プロジェクトが見つかりません",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    backlog_project_id = project.backlog_id
    
    # キャッシュキーを生成
    cache_key = f"project_statuses:{backlog_project_id}:{current_user.id}"
    
    # キャッシュから取得を試みる
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        try:
            statuses = json.loads(cached_data)
            return formatter.success(
                data={
                    "statuses": statuses,
                    "cached": True
                },
                message="ステータス一覧を取得しました（キャッシュ）"
            )
        except json.JSONDecodeError:
            pass
    
    # トークンリフレッシュサービスを使用して有効なトークンを取得
    from app.core.token_refresh import token_refresh_service
    try:
        access_token = await token_refresh_service.ensure_valid_token(current_user, db)
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            detail="Backlog APIトークンの取得に失敗しました",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        # Backlog APIからステータス一覧を取得
        statuses = await backlog_client.get_issue_statuses(
            project_id=backlog_project_id,
            access_token=access_token
        )
        
        # キャッシュに保存（5分間）
        await redis_client.set(cache_key, json.dumps(statuses), expire=300)
        
        # 最終使用日時を更新
        oauth_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == current_user.id,
            OAuthToken.provider == "backlog"
        ).first()
        if oauth_token:
            oauth_token.last_used_at = datetime.utcnow()
            db.commit()
        
        return formatter.success(
            data={
                "statuses": statuses,
                "cached": False
            },
            message="ステータス一覧を取得しました"
        )
        
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.EXTERNAL_API_ERROR,
            detail=f"ステータス一覧の取得に失敗しました: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY
        )


@router.get("/user/project-statuses")
async def get_user_project_statuses(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    formatter: ResponseFormatter = Depends(get_response_formatter)
) -> Dict[str, Any]:
    """
    ユーザーが関わっているプロジェクトのステータス情報を取得
    
    ユーザーがメンバーとして参加している全プロジェクトの
    ステータス情報を集約して返します。
    """
    # ユーザーが参加しているプロジェクトを取得
    from app.models.project import Project, project_members
    projects = db.query(Project).join(project_members).filter(
        project_members.c.user_id == current_user.id
    ).all()
    
    if not projects:
        return formatter.success(
            data={
                "projects": [],
                "all_statuses": []
            },
            message="参加しているプロジェクトがありません"
        )
    
    # トークンリフレッシュサービスを使用して有効なトークンを取得
    from app.core.token_refresh import token_refresh_service
    try:
        access_token = await token_refresh_service.ensure_valid_token(current_user, db)
    except Exception as e:
        raise AppException(
            error_code=ErrorCode.AUTHENTICATION_ERROR,
            detail="Backlog APIトークンの取得に失敗しました",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # 各プロジェクトのステータス情報を収集
    project_statuses = []
    all_statuses_map = {}  # ステータスIDをキーとした重複排除用マップ
    
    for project in projects:
        try:
            # Backlog APIからステータス一覧を取得
            statuses = await backlog_client.get_issue_statuses(
                project_id=project.backlog_id,
                access_token=access_token
            )
            
            project_statuses.append({
                "project_id": project.id,
                "project_name": project.name,
                "backlog_project_id": project.backlog_id,
                "statuses": statuses
            })
            
            # 全ステータスの集約（重複排除）
            for status in statuses:
                all_statuses_map[status['id']] = status
                
        except Exception as e:
            logger.warning(f"Failed to get statuses for project {project.id}: {str(e)}")
            # エラーが発生したプロジェクトはスキップ
            continue
    
    # 全ステータスをリストに変換（displayOrder順）
    all_statuses = sorted(
        all_statuses_map.values(),
        key=lambda x: x.get('displayOrder', 999)
    )
    
    return formatter.success(
        data={
            "projects": project_statuses,
            "all_statuses": all_statuses,
            "cached": False
        },
        message="プロジェクトステータス情報を取得しました"
    )