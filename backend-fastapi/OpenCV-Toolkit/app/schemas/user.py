"""用户资料相关的 Pydantic 模型。"""

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    """个人中心更新资料的请求体。"""

    name: str | None = Field(default=None, min_length=2, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    current_password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        alias="currentPassword",
    )
    new_password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        alias="newPassword",
    )

    class Config:
        populate_by_name = True
