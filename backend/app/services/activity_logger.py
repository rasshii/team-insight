"""
アクティビティログ記録サービス
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import Request

from app.models.user_preferences import ActivityLog
from app.models.user import User


class ActivityLogger:
    """アクティビティログを記録するサービスクラス"""
    
    @staticmethod
    def log_activity(
        db: Session,
        user: User,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> ActivityLog:
        """
        アクティビティログを記録
        
        Args:
            db: データベースセッション
            user: アクティビティを実行したユーザー
            action: アクション名（例: login, logout, update_settings）
            resource_type: リソースタイプ（例: user, project, team）
            resource_id: リソースID
            details: 詳細情報（JSON形式）
            request: HTTPリクエストオブジェクト（IPアドレス取得用）
            
        Returns:
            作成されたActivityLogオブジェクト
        """
        ip_address = None
        if request and request.client:
            ip_address = request.client.host
            
        activity_log = ActivityLog(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(activity_log)
        db.commit()
        db.refresh(activity_log)
        
        return activity_log
    
    @staticmethod
    def log_login(db: Session, user: User, request: Optional[Request] = None):
        """ログインアクティビティを記録"""
        return ActivityLogger.log_activity(
            db=db,
            user=user,
            action="login",
            resource_type="user",
            resource_id=user.id,
            request=request
        )
    
    @staticmethod
    def log_logout(db: Session, user: User, request: Optional[Request] = None):
        """ログアウトアクティビティを記録"""
        return ActivityLogger.log_activity(
            db=db,
            user=user,
            action="logout",
            resource_type="user",
            resource_id=user.id,
            request=request
        )
    
    @staticmethod
    def log_settings_update(
        db: Session, 
        user: User, 
        updated_fields: Dict[str, Any],
        request: Optional[Request] = None
    ):
        """設定更新アクティビティを記録"""
        return ActivityLogger.log_activity(
            db=db,
            user=user,
            action="update_settings",
            resource_type="user",
            resource_id=user.id,
            details={"updated_fields": list(updated_fields.keys())},
            request=request
        )