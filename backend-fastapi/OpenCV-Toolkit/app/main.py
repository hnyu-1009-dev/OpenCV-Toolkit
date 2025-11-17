"""FastAPI 应用入口：负责创建应用、挂载路由及初始化数据库。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db.session import close_db, init_db


def create_application() -> FastAPI:
    """
    创建并返回 FastAPI 实例。

    这样封装的好处：
    - 方便在测试环境中创建新的 app 实例；
    - 保持应用结构清晰，main.py 仅负责启动；
    - 避免在导入阶段执行副作用代码。
    """

    app = FastAPI(
        title=settings.PROJECT_NAME,  # Swagger 文档标题
        version=settings.VERSION,  # 接口版本号
        openapi_url=f"{settings.API_PREFIX}/openapi.json",  # 自定义 OpenAPI 路径
        docs_url=f"{settings.API_PREFIX}/docs",  # Swagger UI 路径
        redoc_url=f"{settings.API_PREFIX}/redoc",  # ReDoc 文档路径
    )

    # -------------------------------------------------------------------------
    # CORS 配置：允许前端跨域访问后台 API
    # -------------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,  # 哪些域名可以访问后端
        allow_credentials=True,  # 允许发送 Cookie / Token
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )

    # -------------------------------------------------------------------------
    # 挂载静态资源目录，用于存储图片等媒体文件
    # 访问方式：/media/<路径>
    # -------------------------------------------------------------------------
    media_dir = Path(__file__).resolve().parents[1] / settings.MEDIA_ROOT
    media_dir.mkdir(parents=True, exist_ok=True)  # 若目录不存在则自动创建

    # 将本地文件夹挂载为静态资源
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    # -------------------------------------------------------------------------
    # 应用启动事件：初始化数据库（Tortoise ORM）
    # -------------------------------------------------------------------------
    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()  # 建立数据库连接、生成表结构等

    # -------------------------------------------------------------------------
    # 应用关闭事件：关闭数据库连接
    # -------------------------------------------------------------------------
    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await close_db()

    # -------------------------------------------------------------------------
    # 注册所有子路由
    # 例：/dashboard/... /vision/... 统一挂载到 /api/v1 之下
    # -------------------------------------------------------------------------
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


# 创建应用实例（供 uvicorn 调用）
app = create_application()
