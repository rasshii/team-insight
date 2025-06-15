from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
import json

class Settings(BaseSettings):
    APP_NAME: str = "Team Insight"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-here"  # 本番環境では必ず変更してください
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/team_insight"

    # Redis設定
    REDIS_URL: str = "redis://redis:6379"

    # CORS設定
    BACKEND_CORS_ORIGINS: Union[str, List[AnyHttpUrl]] = "http://localhost:3000"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Backlog OAuth2.0設定
    BACKLOG_CLIENT_ID: str = ""  # 環境変数から読み込まれます
    BACKLOG_CLIENT_SECRET: str = ""  # 環境変数から読み込まれます
    BACKLOG_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    BACKLOG_SPACE_KEY: str = ""  # BacklogのスペースキーまたはドメインのプレフィックスをOAuth認証時に使用

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
