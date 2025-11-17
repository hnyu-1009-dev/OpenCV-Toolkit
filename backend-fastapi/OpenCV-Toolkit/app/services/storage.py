"""文件存储工具：负责为图库等功能落盘图片."""

from pathlib import Path
import secrets

from fastapi import UploadFile

from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
MEDIA_ROOT = BASE_DIR / settings.MEDIA_ROOT
GALLERY_DIR = MEDIA_ROOT / "gallery"
PREVIEW_DIR = MEDIA_ROOT / "previews"


def ensure_storage_dirs() -> None:
    """保证图库、预览目录存在。"""

    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def _relative_to_media(path: Path) -> str:
    """返回相对 MEDIA_ROOT 的路径，方便与 /media 静态目录对应。"""

    return str(path.relative_to(MEDIA_ROOT).as_posix())


def _build_gallery_filename(user_id: str, original_name: str | None) -> str:
    suffix = Path(original_name or "").suffix or ".img"
    random_part = secrets.token_hex(4)
    return f"{user_id}-{random_part}{suffix}"


async def save_gallery_upload(upload: UploadFile, *, user_id: str) -> str:
    """
    将上传的文件保存到 gallery 目录.

    :return: 返回相对 MEDIA_ROOT 的路径，供静态文件服务与数据库使用
    """

    ensure_storage_dirs()
    filename = _build_gallery_filename(user_id, upload.filename)
    target = GALLERY_DIR / filename
    content = await upload.read()
    target.write_bytes(content)
    await upload.seek(0)
    return _relative_to_media(target)


def save_gallery_bytes(
    content: bytes,
    *,
    user_id: str,
    suffix: str = ".png",
) -> str:
    """保存转换后的图片字节，返回相对路径。"""

    ensure_storage_dirs()
    filename = _build_gallery_filename(user_id, f"processed{suffix}")
    target = GALLERY_DIR / filename
    target.write_bytes(content)
    return _relative_to_media(target)


def save_preview_bytes(content: bytes, *, suffix: str = ".png") -> str:
    """保存临时预览文件，返回相对路径。"""

    ensure_storage_dirs()
    filename = f"preview-{secrets.token_hex(6)}{suffix}"
    target = PREVIEW_DIR / filename
    target.write_bytes(content)
    return _relative_to_media(target)


def delete_media_file(relative_path: str) -> None:
    """根据相对路径删除媒体文件。"""

    ensure_storage_dirs()
    attempt_path = (MEDIA_ROOT / relative_path).resolve()
    media_root_resolved = MEDIA_ROOT.resolve()
    if not str(attempt_path).startswith(str(media_root_resolved)):
        return
    if attempt_path.is_file():
        attempt_path.unlink(missing_ok=True)
