"""图片亮度调节服务：根据前端滑块调整整体亮度。"""

from __future__ import annotations

import cv2
from fastapi import UploadFile

from app.services.scanner import _read_image_with_orientation
from app.services.storage import save_preview_bytes


async def process_brightness_image(
    upload: UploadFile,
    brightness: float,
) -> tuple[str, bytes]:
    """
    根据 brightness 参数调整图片亮度并返回 (预览路径, PNG 字节)。

    brightness 参数:
    - 0 表示保持原始亮度；
    - 正值使画面更亮，负值降低亮度；
    - 推荐范围 -100 ~ 100，对应 OpenCV beta 偏移。
    """

    content = await upload.read()
    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    # 限制亮度偏移，避免出现纯黑或过曝的图像
    beta = max(-100.0, min(100.0, brightness))
    adjusted = cv2.convertScaleAbs(image, alpha=1.0, beta=beta)

    success, buffer = cv2.imencode(".png", adjusted)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    png_bytes = buffer.tobytes()
    await upload.seek(0)
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
