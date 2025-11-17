"""图库相关的 Pydantic 模型。"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GalleryItemBase(BaseModel):
    """图库通用字段。"""

    file_url: str = Field(..., max_length=512, description="图片存储路径 / URL")
    file_name: str | None = Field(
        default=None, max_length=255, description="原始文件名，可选"
    )


class GalleryItemCreate(GalleryItemBase):
    """创建图库记录的请求体。"""

    user_id: str = Field(..., description="关联的用户 ID")


class GalleryItemResponse(GalleryItemBase):
    """返回给前端的图库记录。"""

    id: UUID
    user_id: UUID
    stored_at: datetime

    class Config:
        from_attributes = True


class GalleryItemWithPreview(GalleryItemResponse):
    """包含可访问预览链接的图库记录。"""

    filePreviewUrl: str = Field(..., description="用于前端展示的完整图片 URL")


class GalleryListResponse(BaseModel):
    """图库分页响应。"""

    items: list[GalleryItemWithPreview]
    total: int
    page: int
    page_size: int
    total_pages: int
