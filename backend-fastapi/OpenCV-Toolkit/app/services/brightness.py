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

    brightness 参数说明：
    - 0 表示不改变亮度；
    - >0 图片变亮；
    - <0 图片变暗；
    - 推荐范围为 -100 ~ 100（OpenCV 的 beta 值）。
    """

    # 读取前端上传的图片字节
    content = await upload.read()

    # 使用自定义函数解析图片，并自动处理手机拍照方向
    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    # 限制亮度偏移范围，避免极端值导致图像完全变黑/过曝
    beta = max(-100.0, min(100.0, brightness))

    # 调整亮度：
    # convertScaleAbs 的公式是：output = image * alpha + beta
    # 这里 alpha = 1（不改变对比度），仅添加亮度偏移 beta
    adjusted = cv2.convertScaleAbs(
        image,
        alpha=1.0,  # 对比度不变
        beta=beta,  # 加亮/变暗
    )

    # 编码处理后的图片为 PNG 格式
    success, buffer = cv2.imencode(".png", adjusted)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    # 得到 PNG 字节数据
    png_bytes = buffer.tobytes()

    # 重置上传文件的指针（保证 FastAPI 不报错）
    await upload.seek(0)

    # 保存预览文件到本地 /media，并返回可访问路径
    preview_path = save_preview_bytes(png_bytes, suffix=".png")

    # 返回 (路径, 文件字节)
    return preview_path, png_bytes
