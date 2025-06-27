"""
アプリケーション全体で使用する定数
"""

from enum import Enum


class AuthConstants:
    """認証関連の定数"""
    TOKEN_MAX_AGE = 604800  # 7日間
    OAUTH_STATE_EXPIRY_MINUTES = 10
    COOKIE_NAME = "auth_token"
    COOKIE_PATH = "/"
    COOKIE_SAMESITE = "Lax"
    PROVIDER_BACKLOG = "backlog"


class PaginationConstants:
    """ページネーション関連の定数"""
    DEFAULT_LIMIT = 100
    MAX_LIMIT = 500
    DEFAULT_OFFSET = 0


class CacheConstants:
    """キャッシュ関連の定数"""
    DEFAULT_EXPIRE = 300  # 5分
    LONG_EXPIRE = 3600  # 1時間
    CACHE_KEY_PREFIX = "team_insight:"


class ProjectStatus(str, Enum):
    """プロジェクトステータス"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    """タスクステータス"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ErrorCode(str, Enum):
    """エラーコード"""
    # 認証エラー
    AUTH_TOKEN_NOT_FOUND = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_INVALID_CREDENTIALS = "AUTH_003"
    AUTH_PERMISSION_DENIED = "AUTH_004"
    
    # データエラー
    DATA_NOT_FOUND = "DATA_001"
    DATA_ALREADY_EXISTS = "DATA_002"
    DATA_VALIDATION_ERROR = "DATA_003"
    
    # 外部APIエラー
    EXTERNAL_API_ERROR = "EXT_001"
    EXTERNAL_API_TIMEOUT = "EXT_002"
    
    # システムエラー
    SYSTEM_ERROR = "SYS_001"
    DATABASE_ERROR = "SYS_002"
    INTERNAL_ERROR = "SYS_003"


class ErrorMessages:
    """エラーメッセージ"""
    
    # 認証エラー
    TOKEN_NOT_FOUND = "Backlogアクセストークンが見つかりません。再度ログインしてください。"
    TOKEN_EXPIRED = "アクセストークンの有効期限が切れています。再度ログインしてください。"
    INVALID_CREDENTIALS = "認証情報が無効です。"
    PERMISSION_DENIED = "この操作を実行する権限がありません。"
    AUTHENTICATION_REQUIRED = "認証が必要です。"
    
    # データエラー
    PROJECT_NOT_FOUND = "プロジェクトが見つかりません。"
    USER_NOT_FOUND = "ユーザーが見つかりません。"
    TASK_NOT_FOUND = "タスクが見つかりません。"
    ALREADY_EXISTS = "すでに存在しています。"
    
    # バリデーションエラー
    INVALID_INPUT = "入力値が不正です。"
    LIMIT_EXCEEDED = f"リミットは{PaginationConstants.MAX_LIMIT}以下である必要があります。"
    
    # 外部APIエラー
    BACKLOG_API_ERROR = "Backlog APIの呼び出しに失敗しました。"
    EXTERNAL_SERVICE_UNAVAILABLE = "外部サービスが利用できません。"
    
    # システムエラー
    INTERNAL_SERVER_ERROR = "システムエラーが発生しました。"
    DATABASE_CONNECTION_ERROR = "データベース接続エラーが発生しました。"


class EmailConstants:
    """メール関連の定数"""
    VERIFICATION_TOKEN_LENGTH = 32
    VERIFICATION_TOKEN_EXPIRY_HOURS = 24
    FROM_NAME = "Team Insight"
    VERIFICATION_SUBJECT = "[メールアドレスの確認] Team Insight"
    VERIFICATION_SUCCESS_SUBJECT = "[メールアドレスの確認完了] Team Insight"
