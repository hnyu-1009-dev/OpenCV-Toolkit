"""图库模型：存储用户上传的图片记录。"""

from tortoise import fields
from tortoise.models import Model


class GalleryImage(Model):
    """用来记录用户选择保存到图库的图片."""

    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        'models.User',
        related_name='gallery_images',
        description='关联的上传用户',
    )
    file_url = fields.CharField(max_length=512, description='图片存储地址（本地路径或 OSS URL）')
    file_name = fields.CharField(max_length=255, null=True, description='图片原始文件名')
    stored_at = fields.DatetimeField(auto_now_add=True, description='图片保存时间')
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = 'gallery_images'

