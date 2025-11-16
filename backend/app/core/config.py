from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import os


class Settings(BaseSettings):
    # アプリケーション設定
    APP_NAME: str = "Team Insight"
    DEBUG: bool = Field(default=False, env="DEBUG")
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # セキュリティ設定
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=10080, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 7 days in minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")  # 30 days

    # データベース設定
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/team_insight",
        env="DATABASE_URL",
    )

    # Redis設定
    REDIS_URL: str = Field(default="redis://redis:6379", env="REDIS_URL")
    REDISCLI_AUTH: str = Field(env="REDISCLI_AUTH")
    CACHE_DEFAULT_EXPIRE: int = Field(default=300, env="CACHE_DEFAULT_EXPIRE")  # デフォルト5分
    CACHE_MAX_CONNECTIONS: int = Field(default=20, env="CACHE_MAX_CONNECTIONS")
    CACHE_HEALTH_CHECK_INTERVAL: int = Field(default=30, env="CACHE_HEALTH_CHECK_INTERVAL")

    # Backlog OAuth2.0設定
    BACKLOG_CLIENT_ID: str = Field(default="", env="BACKLOG_CLIENT_ID")
    BACKLOG_CLIENT_SECRET: str = Field(default="", env="BACKLOG_CLIENT_SECRET")
    BACKLOG_REDIRECT_URI: str = Field(default="http://localhost/auth/callback", env="BACKLOG_REDIRECT_URI")
    BACKLOG_SPACE_KEY: str = Field(default="", env="BACKLOG_SPACE_KEY")

    # Backlogアクセス制御設定
    ALLOWED_BACKLOG_SPACES: str = Field(default="", env="ALLOWED_BACKLOG_SPACES")  # カンマ区切りのスペースリスト
    ALLOWED_EMAIL_DOMAINS: str = Field(default="", env="ALLOWED_EMAIL_DOMAINS")  # カンマ区切りのドメインリスト

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

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """SECRET_KEYのセキュリティ検証"""
        # デバッグモードでない場合、より厳格に検証
        is_production = info.data.get("ENVIRONMENT") == "production" or not info.data.get("DEBUG", False)

        if v in ["your-secret-key-here", "changeme", "secret", "password"]:
            raise ValueError(
                "SECRET_KEYに安全でないデフォルト値が設定されています。"
                "強力なランダム文字列を設定してください。"
            )

        if len(v) < 32:
            if is_production:
                raise ValueError("SECRET_KEYは本番環境では最低32文字以上必要です")
            # 開発環境では警告のみ
            import logging
            logging.getLogger(__name__).warning(
                "SECRET_KEYが32文字未満です。本番環境では32文字以上の強力な値を使用してください"
            )

        return v

    @field_validator("REDISCLI_AUTH")
    @classmethod
    def validate_redis_auth(cls, v: str, info) -> str:
        """Redisパスワードのセキュリティ検証"""
        is_production = info.data.get("ENVIRONMENT") == "production" or not info.data.get("DEBUG", False)

        if v in ["redis_password", "password", "changeme", "redis"]:
            raise ValueError(
                "REDISCLI_AUTHに安全でないデフォルト値が設定されています。"
                "強力なパスワードを設定してください。"
            )

        if is_production and len(v) < 16:
            raise ValueError("REDISCLI_AUTHは本番環境では最低16文字以上必要です")

        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """データベースURLのセキュリティ検証"""
        is_production = info.data.get("ENVIRONMENT") == "production" or not info.data.get("DEBUG", False)

        # 本番環境での一般的な安全でない認証情報パターンをチェック
        if is_production:
            unsafe_patterns = [
                "postgres:postgres@",
                "root:root@",
                "admin:admin@",
                "user:password@",
            ]
            for pattern in unsafe_patterns:
                if pattern in v:
                    raise ValueError(
                        f"DATABASE_URLに安全でない認証情報が含まれています: {pattern.split('@')[0]}"
                    )

            if "localhost" in v or "127.0.0.1" in v:
                import logging
                logging.getLogger(__name__).warning(
                    "本番環境でlocalhostのデータベースURLを使用しています"
                )

        return v

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
    """起動時の設定検証（ビジネスロジック関連の検証）"""
    # ロガーを関数内で取得（遅延初期化）
    logger = logging.getLogger(__name__)
    issues = []

    # Backlog認証の検証
    if not settings.BACKLOG_CLIENT_ID or not settings.BACKLOG_CLIENT_SECRET:
        issues.append("Backlog OAuth認証が設定されていません (BACKLOG_CLIENT_IDまたはBACKLOG_CLIENT_SECRETが未設定)")

    # Backlogスペースキーの検証
    if not settings.BACKLOG_SPACE_KEY:
        issues.append("Backlogスペースキーが設定されていません (BACKLOG_SPACE_KEYが未設定)")

    if issues:
        logger.error(f"設定に問題が検出されました: {'; '.join(issues)}")
    else:
        logger.info("設定の検証が正常に完了しました")

    return not bool(issues)
