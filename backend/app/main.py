"""
FastAPIアプリケーションのエントリーポイント

このモジュールは、FastAPIアプリケーションの初期化と設定を行います。
CORS設定、ルーターの登録、データベースの初期化などを含みます。
"""

import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
from app.core.config import settings, validate_settings
from app.api.v1 import api_router
from app.core.cache import CacheMiddleware
from app.core.redis_client import redis_client
from app.api.deps import get_db_session
from app.schemas.health import HealthResponse, ServiceStatus
from app.core.error_handler import register_error_handlers
from app.core.request_id_middleware import RequestIDMiddleware
from app.core.logging_config import setup_logging, get_logger
from app.services.report_scheduler import report_scheduler
from app.services.sync_scheduler import sync_scheduler

# ログ設定を初期化
setup_logging()
logger = get_logger(__name__)


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

    # レポートスケジューラーの起動
    try:
        report_scheduler.start()
        logger.info("レポートスケジューラーが起動されました")
    except Exception as e:
        logger.error(f"レポートスケジューラー起動エラー: {e}")
        # スケジューラーエラーでもアプリケーションは起動を続行

    # 同期スケジューラーの起動
    try:
        sync_scheduler.start()
        logger.info("同期スケジューラーが起動されました")
    except Exception as e:
        logger.error(f"同期スケジューラー起動エラー: {e}")
        # スケジューラーエラーでもアプリケーションは起動を続行

    yield

    # シャットダウン時の処理
    logger.info("アプリケーションをシャットダウンしています...")

    # 同期スケジューラーの停止
    try:
        sync_scheduler.stop()
        logger.info("同期スケジューラーを停止しました")
    except Exception as e:
        logger.error(f"同期スケジューラー停止エラー: {e}")

    # レポートスケジューラーの停止
    try:
        report_scheduler.stop()
        logger.info("レポートスケジューラーを停止しました")
    except Exception as e:
        logger.error(f"レポートスケジューラー停止エラー: {e}")

    # Redis接続の閉じる
    try:
        await redis_client.close()
        logger.info("Redis接続を閉じました")
    except Exception as e:
        logger.error(f"Redis接続クローズエラー: {e}")


app = FastAPI(
    title=settings.APP_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json", lifespan=lifespan, debug=settings.DEBUG
)

# CORS設定
# 重要: CORSミドルウェアは他のミドルウェアより先に設定する必要があります
# 開発環境では異なるポート間でクッキーを共有するため、複数のオリジンを許可
allowed_origins = [settings.FRONTEND_URL]
if settings.DEBUG:
    # 開発環境では、localhost:3000とlocalhostの両方を許可
    allowed_origins.extend(
        [
            "http://localhost",
            "http://localhost:80",
            "http://127.0.0.1",
            "http://127.0.0.1:80",
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # フロントエンドのURLを許可
    allow_credentials=True,  # Cookie認証のため必須
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# リクエストIDミドルウェアの設定
app.add_middleware(RequestIDMiddleware)

# キャッシュミドルウェアの設定
# 認証関連のパスは除外し、APIエンドポイントのみキャッシュ対象とする
app.add_middleware(
    CacheMiddleware,
    default_expire=300,  # 5分
    cacheable_paths=["/api/v1/projects", "/api/v1/teams", "/api/v1/dashboard", "/api/v1/users", "/api/v1/test"],
    exclude_paths=["/api/v1/auth", "/api/v1/cache", "/docs", "/openapi.json"],
)

# エラーハンドラーの登録
register_error_handlers(app)

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to Team Insight API"}


@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db_session)) -> HealthResponse:
    """
    アプリケーションの健全性チェック

    このエンドポイントは、アプリケーション全体の健全性を確認します。
    """
    health_status = {"api": "healthy", "database": "unhealthy", "redis": "unhealthy"}

    # データベース接続チェック
    try:
        # シンプルなクエリを実行してDBの応答を確認
        db.execute(text("SELECT 1"))
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
    overall_status = "healthy" if all(status == "healthy" for status in health_status.values()) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        services=ServiceStatus(**health_status),
        message="Team Insight API is running",
        timestamp=datetime.now(timezone.utc),
    )
