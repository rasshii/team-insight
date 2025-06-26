from fastapi import APIRouter
from app.api.v1 import auth, projects, cache, test, sync, tasks, test_sync, users, analytics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(test.router, prefix="/test", tags=["test"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(test_sync.router, prefix="/test-sync", tags=["test-sync"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
