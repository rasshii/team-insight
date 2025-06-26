"""
FastAPIアプリケーションのエントリーポイント

このモジュールは、FastAPIアプリケーションの初期化と設定を行います。
CORS設定、ルーターの登録、データベースの初期化などを含みます。
"""

import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from app.core.config import settings, validate_settings
from app.api.v1 import api_router
# from app.core.cache import CacheMiddleware  # 一時的に無効化
from app.core.redis_client import redis_client
from app.db.session import get_db
from app.schemas.health import HealthResponse, ServiceStatus

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理

    起動時とシャットダウン時の処理を管理します。
    """
    # 起動時の処理
    logger.info("アプリケーションを起動しています...")
    
    # 設定の検証
    logger.info("設定を検証しています...")
    if not validate_settings():
        logger.warning("設定に問題がありますが、アプリケーションを続行します")
    
    # Redis接続の初期化
    try:
        await redis_client.get_connection()
        logger.info("Redis接続が確立されました")
    except Exception as e:
        logger.error(f"Redis接続エラー: {e}")
        # Redis接続エラーでもアプリケーションは起動を続行

    yield

    # シャットダウン時の処理
    logger.info("アプリケーションをシャットダウンしています...")

    # Redis接続の閉じる
    try:
        await redis_client.close()
        logger.info("Redis接続を閉じました")
    except Exception as e:
        logger.error(f"Redis接続クローズエラー: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


# キャッシュミドルウェアの設定
# 認証関連のパスは除外し、APIエンドポイントのみキャッシュ対象とする
# app.add_middleware(
#     CacheMiddleware,
#     default_expire=300,  # 5分
#     cacheable_paths=[
#         "/api/v1/projects",
#         "/api/v1/teams",
#         "/api/v1/dashboard",
#         "/api/v1/users",
#         "/api/v1/test"
#     ],
#     exclude_paths=[
#         "/api/v1/auth",
#         "/api/v1/cache",
#         "/docs",
#         "/openapi.json"
#     ]
#     )

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Team Insight API"}

@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """
    アプリケーションの健全性チェック

    このエンドポイントは、アプリケーション全体の健全性を確認します。
    """
    health_status = {
        "api": "healthy",
        "database": "unhealthy",
        "redis": "unhealthy"
    }
    
    # データベース接続チェック
    try:
        # シンプルなクエリを実行してDBの応答を確認
        db.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"データベース健全性チェックエラー: {e}")
    
    # Redis接続チェック
    try:
        redis_conn = await redis_client.get_connection()
        await redis_conn.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis健全性チェックエラー: {e}")
    
    # 全体のステータスを判定
    overall_status = "healthy" if all(
        status == "healthy" for status in health_status.values()
    ) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        services=ServiceStatus(**health_status),
        message="Team Insight API is running",
        timestamp=datetime.now(timezone.utc)
    )
