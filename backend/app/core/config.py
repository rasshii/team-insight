from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # アプリケーション設定
    APP_NAME: str = "Team Insight"
    DEBUG: bool = Field(default=False, env="DEBUG")
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")


    # セキュリティ設定
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=10080, env="ACCESS_TOKEN_EXPIRE_MINUTES"  # 7 days in minutes
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30, env="REFRESH_TOKEN_EXPIRE_DAYS"  # 30 days
    )
    
    # データベース設定
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/team_insight",
        env="DATABASE_URL",
    )

    # Redis設定
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDISCLI_AUTH: str = Field(default="redis_password", env="REDISCLI_AUTH")
    CACHE_DEFAULT_EXPIRE: int = Field(
        default=300, env="CACHE_DEFAULT_EXPIRE"
    )  # デフォルト5分
    CACHE_MAX_CONNECTIONS: int = Field(default=20, env="CACHE_MAX_CONNECTIONS")
    CACHE_HEALTH_CHECK_INTERVAL: int = Field(
        default=30, env="CACHE_HEALTH_CHECK_INTERVAL"
    )

    # Backlog OAuth2.0設定
    BACKLOG_CLIENT_ID: str = Field(default="", env="BACKLOG_CLIENT_ID")
    BACKLOG_CLIENT_SECRET: str = Field(default="", env="BACKLOG_CLIENT_SECRET")
    BACKLOG_REDIRECT_URI: str = Field(
        default="http://localhost/auth/callback", env="BACKLOG_REDIRECT_URI"
    )
    BACKLOG_SPACE_KEY: str = Field(default="", env="BACKLOG_SPACE_KEY")
    
    # Backlogアクセス制御設定
    ALLOWED_BACKLOG_SPACES: str = Field(default="", env="ALLOWED_BACKLOG_SPACES")  # カンマ区切りのスペースリスト
    ALLOWED_EMAIL_DOMAINS: str = Field(default="", env="ALLOWED_EMAIL_DOMAINS")    # カンマ区切りのドメインリスト
    
    # CORS設定
    FRONTEND_URL: str = Field(default="http://localhost", env="FRONTEND_URL")
    
    # Email設定（レポート配信用）
    SMTP_HOST: str = Field(default="", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: str = Field(default="", env="SMTP_USER")
    SMTP_PASSWORD: str = Field(default="", env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(default="noreply@teaminsight.dev", env="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field(default="Team Insight Report", env="SMTP_FROM_NAME")
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_SSL: bool = Field(default=False, env="SMTP_SSL")
    
    # 初期管理者設定
    INITIAL_ADMIN_EMAILS: str = Field(default="", env="INITIAL_ADMIN_EMAILS")

    class Config:
        case_sensitive = True
        env_file = ".env"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            # INITIAL_ADMIN_EMAILSをカンマ区切りリストとして解析
            if field_name == "INITIAL_ADMIN_EMAILS":
                return [email.strip() for email in raw_val.split(",") if email.strip()]
            return raw_val


# シングルトンインスタンス
settings = Settings()

# 設定の検証とログ出力
import logging


def validate_settings():
    """起動時の設定検証"""
    # ロガーを関数内で取得（遅延初期化）
    logger = logging.getLogger(__name__)
    issues = []

    # SECRET_KEYの検証
    if settings.SECRET_KEY == "your-secret-key-here":
        if settings.DEBUG:
            logger.warning("デフォルトのSECRET_KEYを使用しています - 本番環境では必ず変更してください")
        else:
            issues.append("本番環境でデフォルトのSECRET_KEYを使用しています")
    elif len(settings.SECRET_KEY) < 32:
        if settings.DEBUG:
            logger.warning("SECRET_KEYが短すぎます（32文字以上を推奨） - 本番環境では必ず強力な値を使用してください")
        else:
            issues.append("本番環境でSECRET_KEYが短すぎます（32文字以上を推奨）")

    # Backlog認証の検証
    if not settings.BACKLOG_CLIENT_ID or not settings.BACKLOG_CLIENT_SECRET:
        issues.append("Backlog OAuth認証が設定されていません (BACKLOG_CLIENT_IDまたはBACKLOG_CLIENT_SECRETが未設定)")

    # Backlogスペースキーの検証
    if not settings.BACKLOG_SPACE_KEY:
        issues.append("Backlogスペースキーが設定されていません (BACKLOG_SPACE_KEYが未設定)")

    # データベースURLの検証
    if "localhost" in settings.DATABASE_URL and not settings.DEBUG:
        issues.append("本番環境でlocalhostのデータベースURLを使用しています")

    # Redis認証の検証
    if settings.REDISCLI_AUTH == "redis_password":
        if settings.DEBUG:
            logger.warning("デバッグモードでデフォルトのRedisパスワードを使用しています - 本番環境では必ず変更してください")
        else:
            issues.append("本番環境でデフォルトのRedisパスワードを使用しています")

    if issues:
        logger.error(f"設定に問題が検出されました: {'; '.join(issues)}")
    else:
        logger.info("設定の検証が正常に完了しました")

    return not bool(issues)
