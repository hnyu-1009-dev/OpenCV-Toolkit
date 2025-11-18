"""图片水印处理工具：将用户上传的水印叠加到原图指定位置。"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np
from fastapi import UploadFile

from app.services.scanner import _read_image_with_orientation
from app.services.storage import save_preview_bytes


def _resize_watermark(
    base_shape: Tuple[int, int],
    watermark: np.ndarray,
) -> np.ndarray:
    """将水印控制在原图约 30% 的宽高，避免遮挡整张图片。"""

    # 原图的高宽
    base_h, base_w = base_shape[:2]

    # 水印的高宽
    wm_h, wm_w = watermark.shape[:2]
    if wm_h == 0 or wm_w == 0:
        raise ValueError("水印图片内容为空")

    # 设定水印在原图中的最大允许尺寸（30%）
    max_w = int(base_w * 0.3)
    max_h = int(base_h * 0.3)

    # 根据限制尺寸计算缩放比例
    scale = min(
        1.0,
        max_w / wm_w if wm_w > 0 else 1.0,
        max_h / wm_h if wm_h > 0 else 1.0,
    )

    # 如果不需要缩放则直接返回
    if scale >= 1.0:
        return watermark

    # 否则按比例缩放水印
    new_size = (max(1, int(wm_w * scale)), max(1, int(wm_h * scale)))
    return cv2.resize(watermark, new_size, interpolation=cv2.INTER_AREA)


async def process_watermark_image(
    base_upload: UploadFile,
    watermark_upload: UploadFile,
    position: tuple[float, float],
    opacity: float = 0.7,
) -> tuple[str, bytes]:
    """
    将水印图片叠加至原图指定位置。

    :param base_upload: 原始图像
    :param watermark_upload: 水印图像
    :param position: (x, y) 归一化坐标，范围 [0, 1]，表示中心点
    :param opacity: 当水印无透明通道时使用的默认透明度
    """

    # 读取原图字节并解析为 OpenCV 图像，同时自动处理方向信息
    base_bytes = await base_upload.read()
    base_image = _read_image_with_orientation(base_bytes)
    if base_image is None:
        raise ValueError("无法解析原始图片")

    # 读取水印字节 → 解码为 BGR 或 BGRA（可能带透明通道）
    watermark_bytes = await watermark_upload.read()
    watermark_array = np.frombuffer(watermark_bytes, dtype=np.uint8)
    watermark_image = cv2.imdecode(watermark_array, cv2.IMREAD_UNCHANGED)
    if watermark_image is None:
        raise ValueError("无法解析水印图片")

    # 将水印按原图大小限制缩放
    watermark_image = _resize_watermark(base_image.shape, watermark_image)

    # 如果水印是灰度图，则扩展为 BGRA
    if watermark_image.ndim == 2:
        watermark_image = cv2.cvtColor(watermark_image, cv2.COLOR_GRAY2BGRA)

    # 根据是否包含透明通道决定使用 alpha mask 或自定义透明度
    if watermark_image.shape[2] == 3:  # 无透明通道 → 使用给定 opacity
        overlay = watermark_image
        alpha_mask = np.full(
            (overlay.shape[0], overlay.shape[1]), opacity, dtype=np.float32
        )
    else:  # 有透明通道 → 使用 alpha 通道作为透明度权重
        alpha_channel = watermark_image[:, :, 3] / 255.0
        overlay = watermark_image[:, :, :3]
        alpha_mask = alpha_channel.astype(np.float32)

    # 获取原图和水印的高宽
    img_h, img_w = base_image.shape[:2]
    wm_h, wm_w = overlay.shape[:2]

    # 归一化坐标限制在 [0,1]
    norm_x, norm_y = position
    norm_x = min(max(norm_x, 0.0), 1.0)
    norm_y = min(max(norm_y, 0.0), 1.0)

    # 计算水印中心点实际像素位置
    center_x = int(norm_x * img_w)
    center_y = int(norm_y * img_h)

    # 将水印定位到中心点，并避免越界
    x0 = int(round(center_x - wm_w / 2))
    y0 = int(round(center_y - wm_h / 2))
    x0 = max(0, min(img_w - wm_w, x0))
    y0 = max(0, min(img_h - wm_h, y0))
    x1 = x0 + wm_w
    y1 = y0 + wm_h

    # 从原图中取出 ROI 区域用于与水印进行混合
    roi = base_image[y0:y1, x0:x1].astype(np.float32)
    overlay_float = overlay.astype(np.float32)

    # 扩展 alpha 到 (h,w,1) 便于三通道广播计算
    alpha_expanded = alpha_mask[..., None]

    # 使用 alpha 混合公式：new = alpha*overlay + (1-alpha)*base
    blended = alpha_expanded * overlay_float + (1 - alpha_expanded) * roi

    # 将混合后的水印写回原图
    base_image[y0:y1, x0:x1] = blended.astype(np.uint8)

    # 编码输出 PNG
    success, buffer = cv2.imencode(".png", base_image)
    if not success:
        raise ValueError("无法编码水印处理后的图片")

    # 恢复文件指针供 FastAPI 再次使用
    await base_upload.seek(0)
    await watermark_upload.seek(0)

    # 保存预览并返回路径与字节
    png_bytes = buffer.tobytes()
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
