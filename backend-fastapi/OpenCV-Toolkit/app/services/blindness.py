"""基于 OpenCV 的色盲模式模拟工具。

流程概览：
- 读取前端上传的 `UploadFile`，解码成 OpenCV 可处理的图像矩阵；
- 根据不同的色盲模式，套用 3x3 颜色变换矩阵模拟色彩感知差异；
- 将结果重新编码为 PNG 字节，存入本地预览目录，并返回对应的文件路径。
"""

from __future__ import annotations

from enum import Enum

import cv2
import numpy as np
from fastapi import UploadFile

from app.services.storage import save_preview_bytes


class ColorBlindMode(str, Enum):
    """与前端保持一致的色盲模式枚举。"""

    red_green = "red_green"
    blue_green = "blue_green"


# 颜色转换矩阵：使用经典的色盲模拟矩阵来调整 RGB 通道
COLOR_BLIND_MATRICES: dict[ColorBlindMode, np.ndarray] = {
    ColorBlindMode.red_green: np.array(
        [
            [0.567, 0.433, 0.0],
            [0.558, 0.442, 0.0],
            [0.0, 0.242, 0.758],
        ],
        dtype=np.float32,
    ),
    ColorBlindMode.blue_green: np.array(
        [
            [0.95, 0.05, 0.0],
            [0.0, 0.433, 0.567],
            [0.0, 0.475, 0.525],
        ],
        dtype=np.float32,
    ),
}


def _apply_matrix_rgb(image_rgb: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    对 RGB 图像施加 3x3 变换矩阵：
    - `image_rgb` 的 shape 为 (H, W, 3)；
    - 使用 `np.tensordot` 将矩阵与每个像素相乘；
    - 结果裁剪到 0-255 并转换回 uint8。
    """

    transformed = np.tensordot(image_rgb.astype(np.float32), matrix.T, axes=1)
    return np.clip(transformed, 0, 255).astype(np.uint8)


def _rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    if not angle:
        return image
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    matrix[0, 2] += (new_w / 2) - center[0]
    matrix[1, 2] += (new_h / 2) - center[1]
    return cv2.warpAffine(
        image,
        matrix,
        (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


async def process_color_blind_image(
    upload: UploadFile,
    mode: ColorBlindMode,
    rotation: float = 0,
) -> tuple[str, bytes]:
    """
    将上传图片转换为指定的色盲模式，返回 (预览路径, PNG 字节)：
    1. 使用 OpenCV 将上传的文件解码成 BGR 图像；
    2. 依据模式切换对应的变换矩阵，对 RGB 图像做颜色调整，再转回 BGR；
    3. 编码成 PNG 字节并写入预览目录，返回相对路径和原始字节。
    """

    content = await upload.read()
    np_arr = np.frombuffer(content, dtype=np.uint8)
    image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("无法解析上传的图片文件")

    matrix = COLOR_BLIND_MATRICES.get(mode)
    if matrix is None:
        raise ValueError(f"Unsupported color blind mode: {mode}")

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    converted_rgb = _apply_matrix_rgb(image_rgb, matrix)
    converted_bgr = cv2.cvtColor(converted_rgb, cv2.COLOR_RGB2BGR)
    rotated = _rotate_image(converted_bgr, rotation)

    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    png_bytes = buffer.tobytes()
    await upload.seek(0)
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
