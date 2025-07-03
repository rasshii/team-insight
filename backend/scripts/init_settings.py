#!/usr/bin/env python3
"""
システム設定の初期データを投入するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.settings import SystemSetting
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_settings(db: Session):
    """デフォルト設定を投入"""
    
    default_settings = [
        # メール設定
        {
            "key": "email_from",
            "value": "noreply@teaminsight.dev",
            "group": "email",
            "value_type": "string",
            "description": "システムメールの送信元アドレス",
            "is_sensitive": False
        },
        {
            "key": "email_from_name",
            "value": "Team Insight",
            "group": "email",
            "value_type": "string",
            "description": "システムメールの送信者名",
            "is_sensitive": False
        },
        
        # セキュリティ設定
        {
            "key": "session_timeout",
            "value": "60",
            "group": "security",
            "value_type": "integer",
            "description": "セッションタイムアウト（分）",
            "is_sensitive": False
        },
        {
            "key": "password_min_length",
            "value": "8",
            "group": "security",
            "value_type": "integer",
            "description": "パスワード最小文字数",
            "is_sensitive": False
        },
        {
            "key": "login_attempt_limit",
            "value": "5",
            "group": "security",
            "value_type": "integer",
            "description": "ログイン失敗によるアカウントロックまでの試行回数",
            "is_sensitive": False
        },
        {
            "key": "api_rate_limit",
            "value": "100",
            "group": "security",
            "value_type": "integer",
            "description": "APIレート制限（リクエスト/分）",
            "is_sensitive": False
        },
        {
            "key": "token_expiry",
            "value": "24",
            "group": "security",
            "value_type": "integer",
            "description": "トークン有効期限（時間）",
            "is_sensitive": False
        },
        
        # 同期設定
        {
            "key": "backlog_sync_interval",
            "value": "60",
            "group": "sync",
            "value_type": "integer",
            "description": "Backlog同期間隔（分）",
            "is_sensitive": False
        },
        {
            "key": "backlog_cache_timeout",
            "value": "300",
            "group": "sync",
            "value_type": "integer",
            "description": "Backlogキャッシュタイムアウト（秒）",
            "is_sensitive": False
        },
        {
            "key": "api_timeout",
            "value": "30",
            "group": "sync",
            "value_type": "integer",
            "description": "APIタイムアウト（秒）",
            "is_sensitive": False
        },
        {
            "key": "max_retry_count",
            "value": "3",
            "group": "sync",
            "value_type": "integer",
            "description": "最大リトライ回数",
            "is_sensitive": False
        },
        
        # システム設定
        {
            "key": "log_level",
            "value": "info",
            "group": "system",
            "value_type": "string",
            "description": "ログレベル（debug, info, warning, error）",
            "is_sensitive": False
        },
        {
            "key": "debug_mode",
            "value": "false",
            "group": "system",
            "value_type": "boolean",
            "description": "開発モード",
            "is_sensitive": False
        },
        {
            "key": "maintenance_mode",
            "value": "false",
            "group": "system",
            "value_type": "boolean",
            "description": "メンテナンスモード",
            "is_sensitive": False
        },
        {
            "key": "data_retention_days",
            "value": "365",
            "group": "system",
            "value_type": "integer",
            "description": "データ保持期間（日）",
            "is_sensitive": False
        },
        {
            "key": "backup_frequency",
            "value": "daily",
            "group": "system",
            "value_type": "string",
            "description": "バックアップ頻度（daily, weekly, monthly）",
            "is_sensitive": False
        }
    ]
    
    for setting_data in default_settings:
        # 既存の設定を確認
        existing = db.query(SystemSetting).filter(
            SystemSetting.key == setting_data["key"]
        ).first()
        
        if not existing:
            setting = SystemSetting(**setting_data)
            db.add(setting)
            logger.info(f"Created setting: {setting_data['key']}")
        else:
            logger.info(f"Setting already exists: {setting_data['key']}")
    
    db.commit()
    logger.info("Settings initialization completed")


if __name__ == "__main__":
    db_gen = get_db()
    db = next(db_gen)
    try:
        init_settings(db)
    finally:
        db.close()