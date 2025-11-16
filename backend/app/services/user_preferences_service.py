"""
ユーザー設定管理サービス
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc
from fastapi import Request

from app.models.user import User
from app.models.user_preferences import UserPreferences, LoginHistory, ActivityLog
from app.schemas.user_preferences import UserPreferencesCreate, UserPreferencesUpdate, UserSettingsUpdate
from app.core.exceptions import NotFoundException, ConflictException, ValidationException

import logging

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """ユーザー設定管理サービス"""

    def get_or_create_preferences(self, db: Session, user_id: int) -> UserPreferences:
        """
        ユーザー設定を取得または作成

        Args:
            db: データベースセッション
            user_id: ユーザーID

        Returns:
            ユーザー設定
        """
        preferences = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

        if not preferences:
            # デフォルト設定で作成
            preferences = UserPreferences(user_id=user_id, email_notifications=True, report_frequency="weekly")
            db.add(preferences)
            db.commit()
            db.refresh(preferences)

        return preferences

    def update_preferences(self, db: Session, user_id: int, update_data: UserPreferencesUpdate) -> UserPreferences:
        """
        ユーザー設定を更新

        Args:
            db: データベースセッション
            user_id: ユーザーID
            update_data: 更新データ

        Returns:
            更新されたユーザー設定
        """
        preferences = self.get_or_create_preferences(db, user_id)

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(preferences, field, value)

        db.commit()
        db.refresh(preferences)

        return preferences

    def update_user_settings(self, db: Session, user_id: int, update_data: UserSettingsUpdate) -> User:
        """
        ユーザー全体の設定を更新

        Args:
            db: データベースセッション
            user_id: ユーザーID
            update_data: 更新データ

        Returns:
            更新されたユーザー
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("ユーザーが見つかりません")

        # 基本情報の更新
        if update_data.name is not None:
            user.name = update_data.name
        if update_data.timezone is not None:
            user.timezone = update_data.timezone
        if update_data.locale is not None:
            user.locale = update_data.locale
        if update_data.date_format is not None:
            user.date_format = update_data.date_format

        # 通知設定の更新
        preferences_update = UserPreferencesUpdate(
            email_notifications=update_data.email_notifications,
            report_frequency=update_data.report_frequency,
            notification_email=update_data.notification_email,
        )

        # Noneでない値のみ更新
        preferences_dict = preferences_update.model_dump(exclude_unset=True)
        if preferences_dict:
            self.update_preferences(db, user_id, preferences_update)

        db.commit()
        db.refresh(user)

        # preferencesをロード
        user.preferences = self.get_or_create_preferences(db, user_id)

        return user

    def record_login(self, db: Session, user_id: int, request: Request, session_id: str) -> LoginHistory:
        """
        ログイン履歴を記録

        Args:
            db: データベースセッション
            user_id: ユーザーID
            request: FastAPIリクエスト
            session_id: セッションID

        Returns:
            ログイン履歴
        """
        login_history = LoginHistory(
            user_id=user_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            session_id=session_id,
        )

        db.add(login_history)
        db.commit()
        db.refresh(login_history)

        # アクティビティログも記録
        self.record_activity(db=db, user_id=user_id, action="login", request=request)

        return login_history

    def record_logout(self, db: Session, user_id: int, session_id: str) -> None:
        """
        ログアウトを記録

        Args:
            db: データベースセッション
            user_id: ユーザーID
            session_id: セッションID
        """
        login_history = (
            db.query(LoginHistory)
            .filter(LoginHistory.user_id == user_id, LoginHistory.session_id == session_id, LoginHistory.logout_at.is_(None))
            .first()
        )

        if login_history:
            login_history.logout_at = datetime.utcnow()
            db.commit()

    def get_login_history(self, db: Session, user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        ログイン履歴を取得

        Args:
            db: データベースセッション
            user_id: ユーザーID
            limit: 取得件数
            offset: オフセット

        Returns:
            ログイン履歴リスト
        """
        query = db.query(LoginHistory).filter(LoginHistory.user_id == user_id).order_by(desc(LoginHistory.login_at))

        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return {"items": items, "total": total, "page": offset // limit + 1, "page_size": limit}

    def record_activity(
        self,
        db: Session,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> ActivityLog:
        """
        アクティビティログを記録

        Args:
            db: データベースセッション
            user_id: ユーザーID
            action: アクション
            resource_type: リソースタイプ
            resource_id: リソースID
            details: 詳細情報
            request: FastAPIリクエスト

        Returns:
            アクティビティログ
        """
        activity_log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.client.host if request and request.client else None,
        )

        db.add(activity_log)
        db.commit()
        db.refresh(activity_log)

        return activity_log

    def get_activity_logs(
        self, db: Session, user_id: int, limit: int = 50, offset: int = 0, action_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        アクティビティログを取得

        Args:
            db: データベースセッション
            user_id: ユーザーID
            limit: 取得件数
            offset: オフセット
            action_filter: アクションフィルター

        Returns:
            アクティビティログリスト
        """
        query = db.query(ActivityLog).filter(ActivityLog.user_id == user_id)

        if action_filter:
            query = query.filter(ActivityLog.action == action_filter)

        query = query.order_by(desc(ActivityLog.created_at))

        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return {"items": items, "total": total, "page": offset // limit + 1, "page_size": limit}

    def get_active_sessions(self, db: Session, user_id: int) -> List[LoginHistory]:
        """
        アクティブなセッション一覧を取得

        Args:
            db: データベースセッション
            user_id: ユーザーID

        Returns:
            アクティブなセッション一覧
        """
        # 最近24時間以内のログインで、ログアウトしていないセッション
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        return (
            db.query(LoginHistory)
            .filter(LoginHistory.user_id == user_id, LoginHistory.logout_at.is_(None), LoginHistory.login_at >= cutoff_time)
            .order_by(desc(LoginHistory.login_at))
            .all()
        )

    def terminate_session(self, db: Session, user_id: int, session_id: str) -> None:
        """
        セッションを終了

        Args:
            db: データベースセッション
            user_id: ユーザーID
            session_id: セッションID
        """
        login_history = (
            db.query(LoginHistory)
            .filter(LoginHistory.user_id == user_id, LoginHistory.session_id == session_id, LoginHistory.logout_at.is_(None))
            .first()
        )

        if login_history:
            login_history.logout_at = datetime.utcnow()
            db.commit()


# シングルトンインスタンス
user_preferences_service = UserPreferencesService()
