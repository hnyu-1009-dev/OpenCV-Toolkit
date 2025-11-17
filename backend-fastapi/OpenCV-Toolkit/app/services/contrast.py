"""图片对比度调节服务：读取前端上传的图片，按照给定比例放大或缩小对比度。"""

from __future__ import annotations

import cv2
from fastapi import UploadFile

from app.services.scanner import _read_image_with_orientation
from app.services.storage import save_preview_bytes


async def process_contrast_image(
    upload: UploadFile,
    contrast: float,
) -> tuple[str, bytes]:
    """
    根据 contrast 比例调整图片对比度并返回 (预览路径, PNG 字节)。

    contrast 参数:
    - 0 表示原始对比度
    - 正值放大对比度（例：0.2 => +20%）
    - 负值降低对比度（例：-0.3 => -30%）
    """

    content = await upload.read()
    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    # 控制对比度增益，避免出现完全黑图或过曝
    gain = max(0.05, min(4.0, 1.0 + contrast))
    adjusted = cv2.convertScaleAbs(image, alpha=gain, beta=0)

    success, buffer = cv2.imencode(".png", adjusted)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    png_bytes = buffer.tobytes()
    await upload.seek(0)
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
