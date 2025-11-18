"""应用配置模块，集中管理环境变量与默认值。"""

from pydantic_settings import BaseSettings  # 用于加载 .env 配置和环境变量
from typing import List  # 为 CORS 列表提供类型提示


class Settings(BaseSettings):
    """
    配置类：
    - 使用 Pydantic 的 BaseSettings 自动读取环境变量
    - 自动从 .env 文件中加载配置
    - 支持类型验证与默认值
    """

    # 项目名称，用于 API 文档等场景显示
    PROJECT_NAME: str = "OpenCV Toolkit Backend"

    # 项目版本号，常用于接口文档显示或版本控制
    VERSION: str = "0.1.0"

    # 统一 API 前缀，例如最终接口是 /api/v1/login
    API_PREFIX: str = "/api/v1"

    # 数据库连接 URL，当前默认使用 SQLite 文件数据库
    DATABASE_URL: str = "sqlite://app.db"

    # 静态文件/用户上传资源存放目录（相对项目根目录）
    MEDIA_ROOT: str = "storage"

    # 后端允许跨域访问的前端源列表
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        # 指定环境变量文件路径（Pydantic 会自动读取该文件）
        env_file = ".env"

        # 指定读取环境变量文件的编码格式
        env_file_encoding = "utf-8"


# 创建全局配置实例
# 其他模块只需 `from app.core.config import settings` 即可使用配置
settings = Settings()
