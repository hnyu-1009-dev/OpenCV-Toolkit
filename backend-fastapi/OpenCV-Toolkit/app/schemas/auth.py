"""认证相关的 Pydantic 模型。"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """登录请求体：仅包含邮箱与密码。"""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(LoginRequest):
    """注册请求体，继承登录字段并扩展个人信息。"""

    name: str = Field(min_length=2, max_length=50)
    confirm_password: str = Field(alias='confirmPassword')
    phone: str | None = None

    class Config:
        populate_by_name = True


class UserInfo(BaseModel):
    """返回给前端显示的用户信息。"""

    id: str
    email: EmailStr
    name: str
    phone: str | None = None


class LoginResponse(BaseModel):
    """登录/注册成功后返回 token 与用户信息。"""

    token: str
    user: UserInfo
