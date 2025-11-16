"""
統一的なログ設定
"""

import logging
import logging.config
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードを構造化JSON形式でフォーマット

        Args:
            record: ログレコード

        Returns:
            JSON形式のログ文字列
        """
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 追加情報がある場合
        if hasattr(record, "extra_data"):
            log_obj["extra"] = record.extra_data

        # エラーの場合、スタックトレースを追加
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # リクエストIDがある場合
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id

        # ユーザーIDがある場合
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id

        return json.dumps(log_obj, ensure_ascii=False)


class SensitiveDataFilter(logging.Filter):
    """機密データをフィルタリングするログフィルター"""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "authorization",
        "cookie",
        "session",
        "credit_card",
        "ssn",
        "email_verification_token",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """
        ログレコードから機密データをマスク

        Args:
            record: ログレコード

        Returns:
            フィルタリング結果（常にTrue）
        """
        # メッセージ内の機密データをマスク
        if hasattr(record, "msg"):
            record.msg = self._mask_sensitive_data(record.msg)

        # 追加データ内の機密データをマスク
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            record.extra_data = self._mask_dict(record.extra_data)

        return True

    def _mask_sensitive_data(self, text: str) -> str:
        """文字列内の機密データをマスク"""
        if not isinstance(text, str):
            return text

        # 簡易的なマスキング（本番環境ではより高度な実装が必要）
        for key in self.SENSITIVE_KEYS:
            if key in text.lower():
                # キー=値のパターンをマスク
                import re

                pattern = rf'{key}["\']?\s*[:=]\s*["\']?([^"\'\s,}}\]]+)'
                text = re.sub(pattern, f"{key}=***MASKED***", text, flags=re.IGNORECASE)

        return text

    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """辞書内の機密データをマスク"""
        masked_data = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked_data[key] = self._mask_dict(value)
            elif isinstance(value, str):
                masked_data[key] = self._mask_sensitive_data(value)
            else:
                masked_data[key] = value
        return masked_data


def setup_logging() -> None:
    """ログ設定をセットアップ"""

    # テスト環境では設定をスキップ（pytestのcaplogと競合を避ける）
    import sys

    if "pytest" in sys.modules:
        return

    # ログレベルの設定
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # ログ設定
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "sensitive_data_filter": {
                "()": SensitiveDataFilter,
            },
        },
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured" if not settings.DEBUG else "simple",
                "filters": ["sensitive_data_filter"],
                "stream": sys.stdout,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": logging.ERROR,
                "formatter": "structured",
                "filters": ["sensitive_data_filter"],
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console"],
            },
            "sqlalchemy": {
                "level": logging.WARNING if not settings.DEBUG else logging.INFO,
                "handlers": ["console"],
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    # ログディレクトリの作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # ログ設定を適用
    logging.config.dictConfig(logging_config)

    # 起動ログ
    logger = logging.getLogger(__name__)
    logger.info(
        "ログシステムを初期化しました",
        extra={
            "extra_data": {
                "log_level": logging.getLevelName(log_level),
                "debug_mode": settings.DEBUG,
                "app_name": settings.APP_NAME,
            }
        },
    )


class LogContext:
    """ログコンテキストマネージャー"""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.old_factory = None

    def __enter__(self):
        """コンテキストを開始"""
        old_factory = logging.getLogRecordFactory()
        self.old_factory = old_factory

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストを終了"""
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得

    Args:
        name: ロガー名

    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(f"app.{name}")
