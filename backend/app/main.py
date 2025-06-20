"""
FastAPIアプリケーションのエントリーポイント

このモジュールは、FastAPIアプリケーションの初期化と設定を行います。
CORS設定、ルーターの登録、データベースの初期化などを含みます。
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.cache import router as cache_router
from app.api.v1.projects import router as projects_router
from app.api.v1.test import router as test_router
from app.core.cache import CacheMiddleware
from app.core.redis_client import redis_client

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

# CORSミドルウェアの設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# キャッシュミドルウェアの設定
# 認証関連のパスは除外し、APIエンドポイントのみキャッシュ対象とする
app.add_middleware(
    CacheMiddleware,
    default_expire=300,  # 5分
    cacheable_paths=[
        "/api/v1/projects",
        "/api/v1/teams",
        "/api/v1/dashboard",
        "/api/v1/users",
        "/api/v1/test"
    ],
    exclude_paths=[
        "/api/v1/auth",
        "/api/v1/cache",
        "/docs",
        "/openapi.json"
    ]
    )

# APIルーターの登録
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(cache_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(test_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Team Insight API"}

@app.get("/health")
async def health_check():
    """
    アプリケーションの健全性チェック

    このエンドポイントは、アプリケーション全体の健全性を確認します。
    """
    try:
        # Redis接続チェック
        redis_conn = await redis_client.get_connection()
        await redis_conn.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis健全性チェックエラー: {e}")
        redis_status = "unhealthy"

    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "redis": redis_status
        },
        "message": "Team Insight API is running"
    }
