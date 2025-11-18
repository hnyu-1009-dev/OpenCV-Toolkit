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
    • OpenCV 的 getPerspectiveTransform 要求输入四点顺序严格一致，否则会出现透视扭曲。
    • 统一顺序可确保透视矫正方向正确。

    排序规则：
    • (x+y) 最小 → 左上
    • (x+y) 最大 → 右下
    • (x-y) 最小 → 右上
    • (x-y) 最大 → 左下
    """

    ordered = np.zeros((4, 2), dtype="float32")

    # 根据 (x+y) 判断左上与右下
    sum_axis = points.sum(axis=1)
    ordered[0] = points[np.argmin(sum_axis)]  # top-left
    ordered[2] = points[np.argmax(sum_axis)]  # bottom-right

    # 根据 (x-y) 判断右上与左下
    diff_axis = np.diff(points, axis=1)
    ordered[1] = points[np.argmin(diff_axis)]  # top-right
    ordered[3] = points[np.argmax(diff_axis)]  # bottom-left

    return ordered


def _apply_scan_effect(warped: np.ndarray) -> np.ndarray:
    """
    对透视后的图像执行“扫描仪风格增强”。

    整体增强流程：
    1) 灰度化 → 为后续处理统一通道
    2) CLAHE → 提升局部对比度
    3) fastNlMeans → 文本区域降噪
    4) 双边滤波 → 平滑背景但保留边缘
    5) normalize → 灰度值线性拉伸到 0~255
    6) adaptiveThreshold → 生成黑白文本掩码
    7) morphology close → 修复文本断裂
    8) bitwise 组合 → 合成“白底 + 黑字”
    9) 锐化 → 文字增强更清晰
    """

    # 1. 转灰度，简化处理
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # 2. 自适应直方图均衡化（提升局部亮度）
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 3. 非局部均值去噪（较强但能保留文本结构）
    denoised = cv2.fastNlMeansDenoising(
        enhanced,
        h=8,
        templateWindowSize=7,
        searchWindowSize=21,
    )

    # 4. 双边滤波（保留文字边缘 + 平滑背景）
    bilateral = cv2.bilateralFilter(
        denoised,
        d=5,
        sigmaColor=60,
        sigmaSpace=70,
    )

    # 5. 将像素值重新拉伸到 0~255 范围
    normalized = cv2.normalize(
        bilateral,
        None,
        0,
        255,
        cv2.NORM_MINMAX,
    )

    # 6. 自适应阈值（生成黑底白字掩码）
    adaptive = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        6,
    )

    # 7. 闭操作 → 补全文字断裂
    morph = cv2.morphologyEx(
        adaptive,
        cv2.MORPH_CLOSE,
        np.ones((2, 2), np.uint8),
        iterations=1,
    )

    # 8. 用掩膜提取文字内容（白色部分是文字）
    text_layer = cv2.bitwise_and(normalized, normalized, mask=morph)

    # 9. 构建白色背景掩膜
    background_mask = cv2.bitwise_not(morph)  # morph=1 是字 → 反转得到背景区域
    background = cv2.bitwise_and(
        np.full_like(normalized, 255),  # 全白
        np.full_like(normalized, 255),
        mask=background_mask,
    )

    # 10. 白底 - 文字 → 得到文字较深、背景全白的效果
    flattened = cv2.subtract(background, text_layer)

    # 11. 文字锐化（让边缘更强）
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(flattened, -1, sharpen_kernel)

    # 12. 转回 BGR 以便保存 PNG
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)


def _rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """旋转图片并自动调整旋转后尺寸，避免出现裁切或黑边。"""

    # 旋转角度为 0 时直接返回原图
    if not angle:
        return image

    # 获取图像高宽
    (h, w) = image.shape[:2]

    # 以图像中心作为旋转中心
    center = (w / 2, h / 2)

    # ---------------------------------------------------------
    # 1. 计算旋转矩阵
    # cv2.getRotationMatrix2D(中心点, 旋转角度, 缩放比例)
    # 返回一个 2x3 的仿射矩阵
    # ---------------------------------------------------------
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # ---------------------------------------------------------
    # 2. 计算旋转后图像的新宽高
    # 公式来源：旋转后的外接矩形尺寸计算
    # abs(cos) 与 abs(sin) 决定了旋转后各边的投影长度
    # ---------------------------------------------------------
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_w = int((h * sin) + (w * cos))  # 新宽度
    new_h = int((h * cos) + (w * sin))  # 新高度

    # ---------------------------------------------------------
    # 3. 调整旋转矩阵的平移量
    # 默认旋转会造成图像偏移，这里手动让图像移动到新的中心
    # ---------------------------------------------------------
    matrix[0, 2] += (new_w / 2) - center[0]
    matrix[1, 2] += (new_h / 2) - center[1]

    # ---------------------------------------------------------
    # 4. 执行仿射变换
    # borderMode=cv2.BORDER_REPLICATE 可以用边缘像素填充空白区域，
    # 避免出现纯黑边
    # ---------------------------------------------------------
    return cv2.warpAffine(
        image,
        matrix,
        (new_w, new_h),  # 输出图像大小（自动扩展）
        flags=cv2.INTER_LINEAR,  # 双线性插值（更平滑）
        borderMode=cv2.BORDER_REPLICATE,  # 边缘填充模式
    )


def _read_image_with_orientation(content: bytes) -> np.ndarray:
    """
    读取图片并根据 EXIF 自动旋转到正确方向。

    • 手机图片通常存储为“旋转信息 + 未旋转像素”
    • exif_transpose 能将图像旋转到正确方向
    """

    image = Image.open(BytesIO(content))

    # 自动根据 EXIF 修正方向
    image = ImageOps.exif_transpose(image)

    # 确保图像为 RGB 模式
    if image.mode != "RGB":
        image = image.convert("RGB")

    # 转换为 OpenCV BGR 格式
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


async def process_document_scan(
    upload: UploadFile,
    points_payload: str,
    rotation: float = 0,
) -> tuple[str, bytes]:
    """
    文档扫描主流程：

    具体步骤：
    1. 解析四点坐标
    2. 读取并自动旋转图片(EXIF)
    3. 将归一化坐标转为像素坐标
    4. 点位排序 → 构建透视变换矩阵
    5. warpPerspective → 拉平文档
    6. 扫描增强（去噪/增强/二值化/白底黑字）
    7. 可选旋转校正
    8. 输出 PNG 字节并保存预览
    """

    # 1. 解析前端传来的点位 JSON
    try:
        raw_points: Iterable[dict[str, float]] = json.loads(points_payload)
    except json.JSONDecodeError as exc:
        raise InvalidScanPoints("points 参数解析失败") from exc

    points = list(raw_points)
    if len(points) != 4:
        raise InvalidScanPoints("points 需要包含四个顶点")

    # 2. 读取上传图像并自动纠正 EXIF 方向
    content = await upload.read()
    image = _read_image_with_orientation(content)
    if image is None:
        raise ValueError("无法解析上传的图片文件")

    # 3. 将归一化坐标转为像素坐标
    height, width = image.shape[:2]
    pts = np.array(
        [[p["x"] * width, p["y"] * height] for p in points],
        dtype="float32",
    )

    # 统一点的顺序（左上→右上→右下→左下）
    ordered = _order_points(pts)

    # 4. 根据选区计算 warp 后目标宽高
    min_x, max_x = float(np.min(ordered[:, 0])), float(np.max(ordered[:, 0]))
    min_y, max_y = float(np.min(ordered[:, 1])), float(np.max(ordered[:, 1]))
    target_width = int(max(1, max_x - min_x))
    target_height = int(max(1, max_y - min_y))

    if target_width == 0 or target_height == 0:
        raise InvalidScanPoints("选区过小，无法生成扫描件")

    # 5. 定义 warp 后的矩形四点
    dst = np.array(
        [
            [0, 0],
            [target_width - 1, 0],
            [target_width - 1, target_height - 1],
            [0, target_height - 1],
        ],
        dtype="float32",
    )

    # 6. 透视变换：拉平文档
    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(image, matrix, (target_width, target_height))

    # 7. 扫描效果增强 + 可选旋转调整
    scanned = _apply_scan_effect(warped)
    rotated = _rotate_image(scanned, rotation)

    # 8. 将处理后的图像编码为 PNG
    success, buffer = cv2.imencode(".png", rotated)
    if not success:
        raise ValueError("无法对处理后的图片进行编码")

    await upload.seek(0)
    png_bytes = buffer.tobytes()

    # 9. 保存预览并返回数据
    preview_path = save_preview_bytes(png_bytes, suffix=".png")
    return preview_path, png_bytes
