from fastapi import APIRouter
from app.api.v1 import auth, projects, cache, test, sync, tasks, users, analytics, backlog, reports, teams, settings, user_settings

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(user_settings.router, prefix="/users", tags=["user-settings"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(test.router, prefix="/test", tags=["test"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(backlog.router, prefix="/backlog", tags=["backlog"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
