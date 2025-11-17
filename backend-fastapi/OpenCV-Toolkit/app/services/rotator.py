"""图片旋转工具：处理前端上传的图片并执行角度旋转。"""

from fastapi import UploadFile

from app.services.scanner import _read_image_with_orientation, _rotate_image
from app.services.storage import save_preview_bytes

import cv2


async def process_rotation_image(
    upload: UploadFile,
    angle: float,
) -> tuple[str, bytes]:
    """
    将图片按角度旋转并返回 (预览路径, PNG 字节)。
    """

    content = await upload.read()
    image = _read_image_with_orientation(content)
    rotated = _rotate_image(image, angle)

    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对旋转后的图片进行编码")

    await upload.seek(0)
    png_bytes = buffer.tobytes()
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
