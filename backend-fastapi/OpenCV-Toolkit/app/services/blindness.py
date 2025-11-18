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
# 这些矩阵来自研究文献，用于模拟不同色觉缺陷时的视觉效果
COLOR_BLIND_MATRICES: dict[ColorBlindMode, np.ndarray] = {
    ColorBlindMode.red_green: np.array(
        [
            [0.567, 0.433, 0.0],  # R 通道的线性混合
            [0.558, 0.442, 0.0],  # G 通道混合
            [0.0, 0.242, 0.758],  # B 通道混合
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
    - 每个像素都是形如 [R, G, B] 的向量；
    - 通过矩阵乘法实现色盲模拟（颜色通道重映射）；
    - tensordot 会将矩阵与每个像素点相乘，比逐像素循环更高效；
    - 最终裁剪到 0-255 并转为 uint8 防止溢出。
    """

    transformed = np.tensordot(image_rgb.astype(np.float32), matrix.T, axes=1)
    return np.clip(transformed, 0, 255).astype(np.uint8)


def _rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """
    将图像按 angle 角度进行旋转。
    - angle 为 0 时直接返回；
    - 使用仿射变换并自动计算旋转后图像的尺寸，使内容不被裁剪；
    - borderMode=REPLICATE 保证旋转后空白区域由边缘像素填充。
    """
    if not angle:
        return image
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)

    # 计算旋转矩阵 (旋转 + 平移)
    matrix = cv2.getRotationMatrix2D(
        center,  # center → 旋转中心坐标（x, y）
        angle,  # angle  → 旋转角度（正值逆时针、负值顺时针）
        1.0,  # 1.0    → 缩放比例（1.0 表示不缩放）
    )

    # 计算旋转后新图像的宽/高，使内容完整不裁剪
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # 调整旋转中心到新画布中心
    matrix[0, 2] += (new_w / 2) - center[0]
    matrix[1, 2] += (new_h / 2) - center[1]

    return cv2.warpAffine(
        image,  # image → 输入图像
        matrix,  # matrix → 2x3 仿射矩阵（旋转 + 平移）
        (new_w, new_h),  # (new_w,new_h) → 输出图像尺寸，保证旋转后不被裁剪
        flags=cv2.INTER_LINEAR,  # 使用双线性插值，使旋转后的图像更平滑（默认最佳选择）
        borderMode=cv2.BORDER_REPLICATE,  # 使用双线性插值，使旋转后的图像更平滑（默认最佳选择）
    )


async def process_color_blind_image(
    upload: UploadFile,
    mode: ColorBlindMode,
    rotation: float = 0,
) -> tuple[str, bytes]:
    """
    将上传图片转换为指定的色盲模式，返回 (预览路径, PNG 字节)：

    主要流程：
    1. 读取上传文件 → 转为 numpy 数组 → 用 OpenCV 解码为 BGR 图像；
    2. 将 BGR 转 RGB（因变换矩阵基于 RGB 空间）；
    3. 根据指定色盲模式执行 3x3 矩阵映射；
    4. 转回 BGR；
    5. 可选：旋转图片；
    6. 编码为 PNG 字节并写入预览目录；
    7. 返回文件路径和 PNG 原始字节。
    """

    # 读取上传文件的二进制内容
    content = await upload.read()
    np_arr = np.frombuffer(content, dtype=np.uint8)

    # 解码得到 BGR 图像（OpenCV 默认格式）
    image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("无法解析上传的图片文件")

    # 获取对应色盲模式的矩阵
    matrix = COLOR_BLIND_MATRICES.get(mode)
    if matrix is None:
        raise ValueError(f"Unsupported color blind mode: {mode}")

    # 转为 RGB 为颜色变换做准备
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    # 应用色盲模拟矩阵
    converted_rgb = _apply_matrix_rgb(image_rgb, matrix)

    # 转回 BGR 提供给 OpenCV 编码
    converted_bgr = cv2.cvtColor(converted_rgb, cv2.COLOR_RGB2BGR)

    # 可选旋转
    rotated = _rotate_image(converted_bgr, rotation)

    # 编码为 PNG
    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    png_bytes = buffer.tobytes()

    # 重置文件指针（保持 UploadFile 的可复用性）
    await upload.seek(0)

    # 保存 PNG 并生成预览文件路径
    preview_path = save_preview_bytes(png_bytes, suffix=".png")

    return preview_path, png_bytes
