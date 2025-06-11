from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    APP_NAME: str = "Team Insight"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # セキュリティ設定
    SECRET_KEY: str = "your-secret-key-here"  # 本番環境では必ず変更してください
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/team_insight"

    # CORS設定
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
