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

    contrast 参数说明：
    - 0  表示不改变对比度；
    - >0 放大对比度，例如 0.2 → 增加 20%；
    - <0 降低对比度，例如 -0.3 → 减少 30%。
    """

    # ----------------------------------------------------------------------
    # 1. 读取上传的图片字节并解析成 OpenCV 图像
    # ----------------------------------------------------------------------
    content = await upload.read()

    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    gain = max(0.05, min(4.0, 1.0 + contrast))

    adjusted = cv2.convertScaleAbs(
        image,
        alpha=gain,  # 控制对比度强度
        beta=0,  # 不修改亮度
    )

    # ----------------------------------------------------------------------
    # 4. 将处理后的图像编码为 PNG 字节
    # ----------------------------------------------------------------------
    success, buffer = cv2.imencode(".png", adjusted)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    png_bytes = buffer.tobytes()

    # 重置上传文件指针，避免 FastAPI 后续继续读取时报错
    await upload.seek(0)

    # ----------------------------------------------------------------------
    # 5. 保存处理后的图片用于前端预览
    # ----------------------------------------------------------------------
    preview_path = save_preview_bytes(png_bytes, suffix=".png")

    return preview_path, png_bytes
