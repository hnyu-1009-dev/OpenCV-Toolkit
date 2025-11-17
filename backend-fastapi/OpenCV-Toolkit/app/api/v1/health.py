"""系统健康检查路由，提供存活检测、自检指标等接口。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="基础健康检查")
async def health_check() -> dict[str, str]:
    """返回简单的 OK ，用于负载均衡或监控系统判断服务状态。"""

    return {"status": "ok"}

