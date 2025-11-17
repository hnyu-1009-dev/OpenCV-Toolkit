"""用户资料相关服务：封装个人中心的读取与更新逻辑。"""

from __future__ import annotations

# from typing import Optional

from tortoise.exceptions import DoesNotExist

from app.models.user import User
from app.schemas.auth import UserInfo
from app.schemas.user import UserProfileUpdate
from app.services.auth import pwd_context


class UserService:
    """提供读取及更新用户资料的方法。"""

    async def get_profile(self, user_id: str) -> UserInfo:
        """根据 ID 返回用户资料。"""

        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        return self._to_user_info(user)

    async def update_profile(
        self,
        user_id: str,
        payload: UserProfileUpdate,
    ) -> UserInfo:
        """根据请求体更新姓名、电话以及可选的密码。"""

        user = await self._get_user(user_id)
        fields_set = payload.model_fields_set

        updated_fields: list[str] = []
        if "name" in fields_set:
            if payload.name is None:
                raise ValueError("姓名不能为空")
            user.name = payload.name
            updated_fields.append("name")

        if "phone" in fields_set:
            user.phone = payload.phone or None
            updated_fields.append("phone")

        if "new_password" in fields_set and payload.new_password:
            if not payload.current_password:
                raise ValueError("修改密码需要填写当前密码")
            if not pwd_context.verify(payload.current_password, user.password):
                raise ValueError("当前密码不正确")
            user.password = pwd_context.hash(payload.new_password)
            updated_fields.append("password")

        if not updated_fields:
            raise ValueError("请至少提供一个需要更新的字段")

        fields_to_save = list(set(updated_fields) | {"updated_at"})
        await user.save(update_fields=fields_to_save)
        return self._to_user_info(user)

    async def _get_user(self, user_id: str) -> User:
        try:
            return await User.get(id=user_id)
        except DoesNotExist as exc:
            raise ValueError("用户不存在") from exc

    def _to_user_info(self, user: User) -> UserInfo:
        return UserInfo(
            id=str(user.id),
            email=user.email,
            name=user.name,
            phone=user.phone,
        )
