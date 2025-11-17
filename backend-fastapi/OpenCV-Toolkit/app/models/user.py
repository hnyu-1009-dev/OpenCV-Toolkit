"""用户模型，使用 Tortoise ORM 定义。"""

from tortoise import fields
from tortoise.models import Model


class User(Model):
    """系统用户表：保存基础账号信息（登录、个人资料等）。"""

    # 主键：UUID 格式，比自增 ID 更安全（不暴露用户数量、不可被轻易枚举）
    id = fields.UUIDField(pk=True)

    # 邮箱：用户登录唯一凭证
    # unique=True → 数据库层唯一索引，确保无法重复注册
    # index=True  → 提升邮箱查询速度
    email = fields.CharField(max_length=255, unique=True, index=True)

    # 哈希后的密码（不可明文存储）
    # 通常使用 bcrypt / passlib 进行加密
    password = fields.CharField(max_length=128)

    # 显示名称（昵称）
    name = fields.CharField(max_length=50)

    # 手机号：可选字段（null=True），用户不一定填写
    phone = fields.CharField(max_length=20, null=True)

    # 创建时间：记录用户注册时间
    # auto_now_add=True → 在插入时自动填入当前时间
    created_at = fields.DatetimeField(auto_now_add=True)

    # 更新时间：用户资料更新时自动刷新（如修改昵称、密码等）
    # auto_now=True → 每次 save() 自动更新
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        # 指定数据库中的真实表名
        table = "users"
