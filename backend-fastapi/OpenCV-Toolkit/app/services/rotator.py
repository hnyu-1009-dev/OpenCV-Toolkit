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

    参数说明：
    - upload：前端上传的图片文件
    - angle：旋转角度，正值逆时针，负值顺时针
    """

    # ----------------------------------------------------------------------
    # 1. 读取上传的图像字节，并解析为 OpenCV 图像
    #    使用 _read_image_with_orientation 自动处理手机照片的方向问题
    # ----------------------------------------------------------------------
    content = await upload.read()
    image = _read_image_with_orientation(content)

    # ----------------------------------------------------------------------
    # 2. 调用内部旋转函数执行旋转
    #    _rotate_image 负责：
    #      - 构建旋转矩阵
    #      - 自动调整旋转后图像尺寸，避免裁切
    # ----------------------------------------------------------------------
    rotated = _rotate_image(image, angle)

    # ----------------------------------------------------------------------
    # 3. 将旋转后的图像编码为 PNG 格式字节
    # ----------------------------------------------------------------------
    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对旋转后的图片进行编码")

    # 重置文件指针，避免 FastAPI 之后再次读取文件时报错
    await upload.seek(0)

    # 编码后的 PNG 字节
    png_bytes = buffer.tobytes()

    # ----------------------------------------------------------------------
    # 4. 保存图像用于前端预览，并返回文件路径 + 图像字节
    # ----------------------------------------------------------------------
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
