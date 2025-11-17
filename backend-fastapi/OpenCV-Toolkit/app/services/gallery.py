"""图库相关的业务逻辑，用于读写 GalleryImage 模型。"""

from datetime import datetime

from app.models.gallery import GalleryImage
from app.services.storage import delete_media_file


async def create_gallery_item(
    *,
    user_id: str,
    file_url: str,
    file_name: str | None = None,
) -> GalleryImage:
    """创建一条图库记录。"""

    return await GalleryImage.create(
        user_id=user_id,
        file_url=file_url,
        file_name=file_name,
    )


async def list_gallery_items_by_user(
    *,
    user_id: str,
    page: int,
    page_size: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> tuple[list[GalleryImage], int]:
    """
    支持分页与日期筛选的图库查询。

    :return: (items, total) -> 当前页数据与总条数
    """

    query = GalleryImage.filter(user_id=user_id)
    if start_at:
        query = query.filter(stored_at__gte=start_at)
    if end_at:
        query = query.filter(stored_at__lte=end_at)

    total = await query.count()
    offset = (page - 1) * page_size
    items = await query.order_by("-stored_at").offset(offset).limit(page_size)
    return items, total


async def delete_gallery_item(
    item_id: str,
    *,
    user_id: str | None = None,
) -> bool:
    """
    删除图库记录（可选限制在用户范围），并尝试移除对应文件。

    :return: 删除成功返回 True，否则 False。
    """

    filters: dict[str, object] = {"id": item_id}
    if user_id:
        filters["user_id"] = user_id

    record = await GalleryImage.filter(**filters).first()
    if not record:
        return False

    await record.delete()
    delete_media_file(record.file_url)
    return True
