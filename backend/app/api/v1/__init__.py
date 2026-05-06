from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    cache,
    organizations,
    projects,
    reports,
    settings,
    system_organizations,
    tasks,
    teams,
    user_settings,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(
    organizations.router, prefix="/organizations", tags=["organizations"]
)
api_router.include_router(
    system_organizations.router,
    prefix="/system/organizations",
    tags=["system-organizations"],
)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
# user_settings.routerを先に登録（/users/me が /users/{user_id} より優先されるように）
api_router.include_router(user_settings.router, prefix="/users", tags=["user-settings"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
