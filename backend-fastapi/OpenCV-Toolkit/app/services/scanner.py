"""文档扫描相关处理逻辑：负责透视矫正、图像增强并输出扫描件风格的图片。"""

from __future__ import annotations

import json
from io import BytesIO
from typing import Iterable

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image, ImageOps

from app.services.storage import save_preview_bytes


class InvalidScanPoints(ValueError):
    """当前端传入的点无效（格式错误、解析失败或点数量不为 4）时抛出此异常。"""


def _order_points(points: np.ndarray) -> np.ndarray:
    """
    对四边形的顶点进行排序，输出顺序固定为：
    左上 (tl)、右上 (tr)、右下 (br)、左下 (bl)。

    为什么要排序？
    • OpenCV 的透视变换（getPerspectiveTransform）要求输入的四点顺序严格一致。
    • 任意顺序会导致透视拉伸、镜像或扭曲。

    排序规则：
    • 点的 (x + y) 最小 → 左上
    • 点的 (x + y) 最大 → 右下
    • 点的 (x - y) 最小 → 右上
    • 点的 (x - y) 最大 → 左下
    """

    ordered = np.zeros((4, 2), dtype="float32")

    # (x + y) 最小的是左上，最大的是右下
    sum_axis = points.sum(axis=1)
    ordered[0] = points[np.argmin(sum_axis)]  # top-left
    ordered[2] = points[np.argmax(sum_axis)]  # bottom-right

    # (x - y) 最小的是右上，最大的是左下
    diff_axis = np.diff(points, axis=1)
    ordered[1] = points[np.argmin(diff_axis)]  # top-right
    ordered[3] = points[np.argmax(diff_axis)]  # bottom-left

    return ordered


def _apply_scan_effect(warped: np.ndarray) -> np.ndarray:
    """
    对透视后的图像执行扫描增强，使其更接近手机扫描仪的效果。

    增强流程：
    1) CLAHE → 提升局部对比度
    2) fastNlMeans → 去噪但保留文字边缘
    3) 双边滤波 → 进一步平滑背景而不模糊文字
    4) normalize → 标准化亮度范围
    5) adaptiveThreshold → 获取文本掩码（黑白）
    6) morphologyEx → 修复字迹断裂
    7) bitwise 操作合成“白底 + 黑字”
    8) unsharp mask → 文字锐化
    """

    # 1. 灰度化（之后的算法都基于灰度）
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # 2. 提升局部亮度对比度
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 3. 非局部均值降噪（手机扫描中非常有效）
    denoised = cv2.fastNlMeansDenoising(
        enhanced,
        h=8,  # 去噪强度（越大越平滑）
        templateWindowSize=7,  # 用于比较的局部块大小
        searchWindowSize=21,  # 搜索区域大小
    )

    # 4. 双边滤波（平滑背景 + 保留边缘）
    bilateral = cv2.bilateralFilter(
        denoised,
        d=5,  # 邻域直径
        sigmaColor=60,  # 颜色差越小越容易被平滑
        sigmaSpace=70,  # 距离越近权重越大
    )

    # 5. 亮度归一化为 0～255
    # 对双边滤波后的图像执行线性归一化，将其灰度值重新压缩到 0~255 范围。
    normalized = cv2.normalize(
        bilateral,  # 输入图像
        None,  # 输出（不传则自动创建）
        0,  # 映射后的最小灰度值
        255,  # 映射后的最大灰度值
        cv2.NORM_MINMAX,  # 线性拉伸：new = (img - min) / (max - min) * 255
    )

    # 6. 基于局部亮度的自适应阈值 → 获得黑白文本掩码
    adaptive = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,  # 高斯加权
        cv2.THRESH_BINARY_INV,  # 黑白图
        11,  # 邻域块尺寸
        6,  # 调整常数
    )

    # 7. 闭操作：使文字边缘更加连贯
    morph = cv2.morphologyEx(
        adaptive,
        cv2.MORPH_CLOSE,
        np.ones((2, 2), np.uint8),
        iterations=1,
    )

    # 8. 使用阈值图作为 mask，从原图提取文字区域
    text_layer = cv2.bitwise_and(normalized, normalized, mask=morph)

    # 9. 白色背景区域（即 morph=0 的地方）
    background_mask = cv2.bitwise_not(morph)
    background = cv2.bitwise_and(
        np.full_like(normalized, 255),
        np.full_like(normalized, 255),
        mask=background_mask,
    )

    # 10. 文本层 + 白底层合成扫描结果
    # flattened = cv2.add(text_layer, background)
    flattened = cv2.subtract(background, text_layer)

    # 11. 使用锐化卷积核增强文字边缘
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(flattened, -1, sharpen_kernel)

    # 转成 BGR，便于后续压缩编码
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)


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


def _read_image_with_orientation(content: bytes) -> np.ndarray:
    """
    读取图片并自动纠正 EXIF 方向。

    • 手机拍摄的图片往往储存为“旋转后的 EXIF 标记”
    • 需要通过 exif_transpose 变换成真实方向
    """

    image = Image.open(BytesIO(content))

    # 自动根据 EXIF 调整正确方向
    image = ImageOps.exif_transpose(image)

    # 转为 RGB（有些图片可能是 CMYK 或灰度）
    if image.mode != "RGB":
        image = image.convert("RGB")

    # 转换为 OpenCV 的 BGR 图
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


async def process_document_scan(
    upload: UploadFile,
    points_payload: str,
    rotation: float = 0,
) -> tuple[str, bytes]:
    """
    文档扫描主流程：
    1) 解析四点坐标
    2) 读取图片并纠正方向
    3) 将四点映射到像素坐标
    4) 构建透视变换矩阵
    5) warpPerspective 拉平为矩形图
    6) 执行扫描风格增强
    7) 输出 PNG 二进制和预览路径
    """

    # -------------------------------------------------------
    # 1. 解析前端传入的 points JSON
    # -------------------------------------------------------
    try:
        raw_points: Iterable[dict[str, float]] = json.loads(points_payload)
    except json.JSONDecodeError as exc:
        raise InvalidScanPoints("points 参数解析失败") from exc

    points = list(raw_points)
    if len(points) != 4:
        raise InvalidScanPoints("points 需要包含四个顶点")

    # -------------------------------------------------------
    # 2. 读取上传图片（含 EXIF 校正）
    # -------------------------------------------------------
    content = await upload.read()
    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    # -------------------------------------------------------
    # 3. 将归一化坐标（0~1）转为真实像素坐标
    # -------------------------------------------------------
    height, width = image.shape[:2]

    pts = np.array(
        [[p["x"] * width, p["y"] * height] for p in points],
        dtype="float32",
    )

    # 统一点位顺序
    ordered = _order_points(pts)

    # -------------------------------------------------------
    # 4. 自动计算 warp 后的目标宽高（取 bounding box）
    # -------------------------------------------------------
    min_x = float(np.min(ordered[:, 0]))
    max_x = float(np.max(ordered[:, 0]))
    min_y = float(np.min(ordered[:, 1]))
    max_y = float(np.max(ordered[:, 1]))

    target_width = int(max(1, max_x - min_x))
    target_height = int(max(1, max_y - min_y))

    if target_width == 0 or target_height == 0:
        raise InvalidScanPoints("选区过小，无法生成扫描件")

    # -------------------------------------------------------
    # 5. 构建目标矩形四点，用于透视矫正
    # -------------------------------------------------------
    dst = np.array(
        [
            [0, 0],  # 左上
            [target_width - 1, 0],  # 右上
            [target_width - 1, target_height - 1],  # 右下
            [0, target_height - 1],  # 左下
        ],
        dtype="float32",
    )

    # -------------------------------------------------------
    # 6. 计算透视变换矩阵，并执行 warp
    # -------------------------------------------------------
    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(
        image,
        matrix,
        (target_width, target_height),
    )

    # -------------------------------------------------------
    # 7. 扫描风格增强
    # -------------------------------------------------------
    scanned = _apply_scan_effect(warped)
    rotated = _rotate_image(scanned, rotation)

    # -------------------------------------------------------
    # 8. 编码 PNG 输出
    # -------------------------------------------------------
    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    await upload.seek(0)  # 重置文件指针，避免后续读取失败
    png_bytes = buffer.tobytes()

    # -------------------------------------------------------
    # 9. 保存预览图（本地）并返回
    # -------------------------------------------------------
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
