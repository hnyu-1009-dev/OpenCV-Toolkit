"""Tortoise ORM 初始化与关闭逻辑，并兼容 Aerich 迁移工具。"""

from tortoise import Tortoise

from app.core.config import settings

# 统一的 ORM 配置：Aerich 使用同一份配置
TORTOISE_ORM_CONFIG = {
    "connections": {
        # 读取 .env 中的 DATABASE_URL，默认 sqlite://app.db
        "default": "mysql://root:mysql030721@localhost:3306/opencv_toolkid_db",
    },
    "apps": {
        "models": {
            # 业务模型 + aerich 内置模型，用于记录迁移历史
            "models": ["app.models.user", "app.models.gallery", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}


async def init_db() -> None:
    """启动 FastAPI 时调用，建立数据库连接并创建表结构。"""

    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    await Tortoise.generate_schemas()


async def close_db() -> None:
    """关闭应用时调用，释放数据库连接。"""

    await Tortoise.close_connections()
