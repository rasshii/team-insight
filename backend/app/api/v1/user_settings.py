"""
ユーザー設定APIエンドポイント

個人ユーザーが自分の設定を管理するためのエンドポイント
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db_session, get_current_active_user
from app.models.user import User
from app.schemas.user_preferences import (
    UserSettings,
    UserSettingsUpdate,
    UserPreferences,
    UserPreferencesUpdate,
    LoginHistoryListResponse,
    ActivityLogListResponse,
    SessionInfo
)
from app.services.user_preferences_service import user_preferences_service
from app.core.deps import get_response_formatter
from app.core.response_builder import ResponseFormatter
from app.core.error_handler import AppException, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me")
async def get_my_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーの設定を取得
    """
    logger.info(f"get_my_settings called for user: {current_user.id}")
    # preferencesを取得または作成
    current_user.preferences = user_preferences_service.get_or_create_preferences(
        db, current_user.id
    )
    
    try:
        # UserSettingsスキーマを手動で構築
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "backlog_id": current_user.backlog_id,
            "is_active": current_user.is_active,
            "timezone": current_user.timezone,
            "locale": current_user.locale,
            "date_format": current_user.date_format,
            "preferences": None
        }
        
        # preferencesが存在する場合は追加
        if current_user.preferences:
            user_data["preferences"] = {
                "id": current_user.preferences.id,
                "user_id": current_user.preferences.user_id,
                "email_notifications": current_user.preferences.email_notifications,
                "report_frequency": current_user.preferences.report_frequency,
                "notification_email": current_user.preferences.notification_email,
                "created_at": current_user.preferences.created_at,
                "updated_at": current_user.preferences.updated_at
            }
        
        user_settings = UserSettings.model_validate(user_data)
        return formatter.success(data=user_settings.model_dump())
    except Exception as e:
        logger.error(f"Error validating user settings: {e}", exc_info=True)
        raise


@router.put("/me")
async def update_my_settings(
    settings_update: UserSettingsUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーの設定を更新
    """
    updated_user = user_preferences_service.update_user_settings(
        db, current_user.id, settings_update
    )
    
    # アクティビティログを記録
    user_preferences_service.record_activity(
        db=db,
        user_id=current_user.id,
        action="update_settings",
        resource_type="user",
        resource_id=current_user.id,
        details=settings_update.model_dump(exclude_unset=True),
        request=request
    )
    
    # UserSettingsスキーマを手動で構築
    user_data = {
        "id": updated_user.id,
        "email": updated_user.email,
        "name": updated_user.name,
        "backlog_id": updated_user.backlog_id,
        "is_active": updated_user.is_active,
        "timezone": updated_user.timezone,
        "locale": updated_user.locale,
        "date_format": updated_user.date_format,
        "preferences": None
    }
    
    # preferencesが存在する場合は追加
    if updated_user.preferences:
        user_data["preferences"] = {
            "id": updated_user.preferences.id,
            "user_id": updated_user.preferences.user_id,
            "email_notifications": updated_user.preferences.email_notifications,
            "report_frequency": updated_user.preferences.report_frequency,
            "notification_email": updated_user.preferences.notification_email,
            "created_at": updated_user.preferences.created_at,
            "updated_at": updated_user.preferences.updated_at
        }
    
    return formatter.success(
        data=UserSettings.model_validate(user_data).model_dump(),
        message="設定を更新しました"
    )


@router.get("/me/preferences")
async def get_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーの通知設定を取得
    """
    preferences = user_preferences_service.get_or_create_preferences(
        db, current_user.id
    )
    
    return formatter.success(data=preferences)


@router.put("/me/preferences")
async def update_my_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーの通知設定を更新
    """
    updated_preferences = user_preferences_service.update_preferences(
        db, current_user.id, preferences_update
    )
    
    return formatter.success(
        data=updated_preferences,
        message="通知設定を更新しました"
    )


@router.get("/me/login-history")
async def get_my_login_history(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーのログイン履歴を取得
    """
    offset = (page - 1) * page_size
    result = user_preferences_service.get_login_history(
        db, current_user.id, limit=page_size, offset=offset
    )
    
    return formatter.success(data=result)


@router.get("/me/activity-logs")
async def get_my_activity_logs(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(50, ge=1, le=100, description="1ページあたりの件数"),
    action: Optional[str] = Query(None, description="アクションでフィルタ"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーのアクティビティログを取得
    """
    offset = (page - 1) * page_size
    result = user_preferences_service.get_activity_logs(
        db, current_user.id, limit=page_size, offset=offset, action_filter=action
    )
    
    return formatter.success(data=result)


@router.get("/me/sessions")
async def get_my_sessions(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    現在のユーザーのアクティブセッション一覧を取得
    """
    active_sessions = user_preferences_service.get_active_sessions(db, current_user.id)
    
    # 現在のセッションIDを取得（Cookieから）
    current_session_id = request.cookies.get("session_id", "")
    
    sessions = []
    for session in active_sessions:
        sessions.append(SessionInfo(
            session_id=session.session_id or "",
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            login_at=session.login_at,
            is_current=session.session_id == current_session_id
        ))
    
    return formatter.success(data={"sessions": sessions})


@router.delete("/me/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
    formatter: ResponseFormatter = Depends(get_response_formatter)
):
    """
    指定されたセッションを終了
    """
    # 現在のセッションは終了できない
    current_session_id = request.cookies.get("session_id", "")
    if session_id == current_session_id:
        raise AppException(
            error_code=ErrorCode.VALIDATION_ERROR,
            detail="現在のセッションは終了できません",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    user_preferences_service.terminate_session(db, current_user.id, session_id)
    
    # アクティビティログを記録
    user_preferences_service.record_activity(
        db=db,
        user_id=current_user.id,
        action="terminate_session",
        details={"session_id": session_id},
        request=request
    )
    
    return formatter.success(message="セッションを終了しました")