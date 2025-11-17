"""统一对外的 API 路由入口。"""

from fastapi import APIRouter

from app.api.v1 import auth, health, dashboard, user

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard.router)  # /dashboard/...
api_router.include_router(user.router)  # /users/...
