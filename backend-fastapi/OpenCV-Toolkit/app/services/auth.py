"""鉴权服务：使用 Tortoise ORM 操作数据库。"""

import uuid
from typing import Optional

from passlib.context import CryptContext
from tortoise.exceptions import IntegrityError

from app.models.user import User
from app.schemas.auth import LoginResponse, RegisterRequest, UserInfo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """负责处理登录与注册逻辑。"""

    async def login(
        self,
        email: str,
        password: str,
    ) -> Optional[LoginResponse]:
        """根据邮箱查找用户并比对密码。"""

        user = await User.get_or_none(email=email)
        if not user or not pwd_context.verify(password, user.password):
            return None
        return self._build_login_response(user)

    async def register(self, payload: RegisterRequest) -> LoginResponse:
        """注册新用户，成功后直接返回登录凭据。"""

        if payload.password != payload.confirm_password:
            raise ValueError("两次输入的密码不一致")

        existing = await User.get_or_none(email=payload.email)
        if existing:
            if not pwd_context.verify(payload.password, existing.password):
                raise ValueError("该邮箱已注册，请直接登录")
            return self._build_login_response(existing)

        hashed_password = pwd_context.hash(payload.password)
        try:
            user = await User.create(
                email=payload.email,
                password=hashed_password,
                name=payload.name,
                phone=payload.phone,
            )
        except IntegrityError as exc:
            raise ValueError("该邮箱已注册，请直接登录") from exc

        return self._build_login_response(user)

    def _build_login_response(self, user: User) -> LoginResponse:
        """封装统一的登录响应结构。"""

        return LoginResponse(
            token=self._fake_token(str(user.id)),
            user=UserInfo(
                id=str(user.id),
                email=user.email,
                name=user.name,
                phone=user.phone,
            ),
        )

    def _fake_token(self, subject: str) -> str:
        """暂时生成一个伪 token，后续可接入 JWT。"""

        return f"fake-token-for-{subject}-{uuid.uuid4()}"
