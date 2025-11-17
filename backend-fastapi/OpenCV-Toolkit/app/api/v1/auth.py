"""鉴权相关路由：注册、登录等。"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(payload: LoginRequest, service: AuthService = Depends()):
    """调用服务层校验邮箱密码并返回令牌。"""

    user = await service.login(payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
        )
    return user


@router.post("/register", response_model=LoginResponse, summary="用户注册")
async def register(payload: RegisterRequest, service: AuthService = Depends()):
    """简单注册流程，返回与登录相同的结构，方便前端直接登录。"""

    try:
        return await service.register(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
