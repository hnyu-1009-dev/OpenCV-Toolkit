"""仪表盘 / 工作台 API。"""

import math
import json
from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile

from app.schemas.gallery import (
    GalleryItemCreate,
    GalleryItemResponse,
    GalleryItemWithPreview,
    GalleryListResponse,
)
from app.services.blindness import ColorBlindMode, process_color_blind_image
from app.services.brightness import process_brightness_image
from app.services.gallery import (
    create_gallery_item,
    delete_gallery_item,
    list_gallery_items_by_user,
)
from app.services.scanner import InvalidScanPoints, process_document_scan
from app.services.rotator import process_rotation_image
from app.services.contrast import process_contrast_image
from app.services.watermark import process_watermark_image
from app.services.storage import save_gallery_bytes, save_gallery_upload

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _media_url(request: Request, path: str) -> str:
    """辅助函数：构造静态资源的完整 URL。"""

    return str(request.url_for('media', path=path))


def _preview_payload(request: Request, record) -> dict:
    """将 ORM 记录转换为带预览链接的响应字典。"""

    base = GalleryItemResponse.model_validate(record)
    preview = GalleryItemWithPreview(
        **base.model_dump(),
        filePreviewUrl=_media_url(request, base.file_url),
    )
    return preview.model_dump()


@router.get("/summary", summary="仪表盘概览")
async def dashboard_summary() -> dict[str, int]:
    """返回一些占位指标，前端可在工作台首页展示。"""

    return {"tasks": 0, "gallery_items": 0, "pipelines": 0}


@router.post("/gallery", summary="保存图片元数据", response_model=GalleryItemResponse)
async def save_gallery_item(payload: GalleryItemCreate) -> GalleryItemResponse:
    """当前端已有图片路径时，直接调用此接口写入图库记录。"""

    record = await create_gallery_item(
        user_id=payload.user_id,
        file_url=payload.file_url,
        file_name=payload.file_name,
    )
    return GalleryItemResponse.model_validate(record)


@router.post(
    "/gallery/upload",
    summary="上传并保存图片至图库",
    response_model=GalleryItemResponse,
)
async def upload_gallery_item(
    user_id: str = Form(..., description="图片所属用户 ID"),
    file: UploadFile = File(...),
) -> GalleryItemResponse:
    """处理前端上传的原始图片：保存到磁盘并创建图库记录。"""

    stored_path = await save_gallery_upload(file, user_id=user_id)
    record = await create_gallery_item(
        user_id=user_id,
        file_url=stored_path,
        file_name=file.filename,
    )
    return GalleryItemResponse.model_validate(record)


@router.get(
    "/gallery/{user_id}",
    summary="查询用户图库",
    response_model=GalleryListResponse,
)
async def list_gallery_items(
    request: Request,
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    start_date: date | None = Query(None, description="起始日期 (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="结束日期 (YYYY-MM-DD)"),
) -> GalleryListResponse:
    """根据用户 ID 拉取图库条目，可分页和按照添加日期筛选。"""

    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None

    items, total = await list_gallery_items_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
        start_at=start_dt,
        end_at=end_dt,
    )

    total_pages = math.ceil(total / page_size) if total else 0
    previews = [_preview_payload(request, item) for item in items]

    return GalleryListResponse(
        items=previews,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.delete(
    "/gallery/{item_id}",
    summary="删除图库图片",
    status_code=204,
)
async def remove_gallery_item(
    item_id: UUID,
    user_id: str | None = Query(None, description="可选：限制为当前用户的记录"),
) -> None:
    """删除图库图片，如果提供 user_id 则校验归属。"""

    deleted = await delete_gallery_item(str(item_id), user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="图片不存在或无权删除")


@router.post(
    "/vision/color-blind",
    summary="色盲模式转换",
    description="上传图片后模拟指定色盲模式，可选将原图 / 处理图保存到图库。",
)
async def color_blind_transform(
    request: Request,
    mode: ColorBlindMode = Form(..., description="色盲模式，与前端枚举保持一致"),
    file: UploadFile = File(..., description="待处理图片文件"),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存处理图到图库"),
    user_id: str | None = Form(
        default=None,
        description="当前登录用户 ID，保存图库时必须提供",
    ),
    rotation: float = Form(default=0, description="追加旋转角度（度）"),
) -> dict:
    """
    对上传图片执行色盲转换，并按需将图片写入图库。

    返回字段：
    - processedImage：处理后的图片 URL，可直接交给 <img>；
    - savedOriginal / savedProcessed：当保存选项开启时，返回对应的图库记录。
    """

    try:
        preview_path, processed_bytes = await process_color_blind_image(file, mode, rotation)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="图片处理失败，请确认文件是否为有效图片") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"processed-{file.filename or 'image.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "mode": mode.value,
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }


@router.post(
    "/vision/document-scan",
    summary="扫描件生成",
    description="上传图片后框选区域，执行透视矫正与扫描风处理。",
)
async def document_scan(
    request: Request,
    file: UploadFile = File(..., description="待处理原图"),
    points: str = Form(..., description="四个角点坐标(JSON 数组，坐标为 0-1 范围)"),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存扫描件到图库"),
    user_id: str | None = Form(default=None, description="当前登录用户 ID"),
    rotation: float = Form(default=0, description="扫描结果追加旋转角度"),
) -> dict:
    """执行文档扫描流程。"""

    try:
        preview_path, processed_bytes = await process_document_scan(file, points, rotation)
    except InvalidScanPoints as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="扫描处理失败，请检查文件与选区") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"scan-{file.filename or 'document.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }


@router.post(
    "/vision/rotate",
    summary="图片旋转",
    description="上传图片后按照指定角度进行旋转，可选保存到图库。",
)
async def rotate_image(
    request: Request,
    file: UploadFile = File(..., description="待旋转图片"),
    rotation: float = Form(..., description="旋转角度（度）"),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存旋转图"),
    user_id: str | None = Form(default=None, description="当前登录用户 ID"),
) -> dict:
    """执行简单图片旋转。"""

    try:
        preview_path, processed_bytes = await process_rotation_image(file, rotation)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="图片旋转失败，请确认文件是否有效") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"rotate-{file.filename or 'image.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }


@router.post(
    "/vision/watermark",
    summary="图片水印添加",
    description="上传原图与水印图，指定点击位置后生成带水印图片。",
)
async def watermark_image(
    request: Request,
    file: UploadFile = File(..., description="待添加水印的原图"),
    watermark: UploadFile = File(..., description="水印图片，建议 PNG 以便保留透明度"),
    position: str = Form(..., description='JSON 字符串，例如 {"x":0.5,"y":0.5}，坐标范围 0-1'),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存处理结果到图库"),
    user_id: str | None = Form(default=None, description="当前登录用户 ID"),
) -> dict:
    """根据指定坐标将水印叠加到原图。"""

    try:
        payload = json.loads(position)
        pos_x = float(payload["x"])
        pos_y = float(payload["y"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="position 参数格式不正确，应包含 x/y 归一化坐标") from exc

    try:
        preview_path, processed_bytes = await process_watermark_image(
            file,
            watermark,
            (pos_x, pos_y),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="水印处理失败，请确认图片文件有效") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"watermark-{file.filename or 'image.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }


@router.post(
    "/vision/contrast",
    summary="图片对比度调节",
    description="上传图片后通过对比度系数增强或减弱细节，对比度值范围建议在 -1.0~1.0 之间",
)
async def adjust_contrast(
    request: Request,
    file: UploadFile = File(..., description="待处理图片"),
    contrast: float = Form(..., description="对比度系数，0 表示不变，正值增强、负值减弱"),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存调整结果到图库"),
    user_id: str | None = Form(default=None, description="当前登录用户 ID"),
) -> dict:
    """根据指定系数调整图片对比度。"""

    try:
        preview_path, processed_bytes = await process_contrast_image(file, contrast)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="对比度调节失败，请确认文件是否有效") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"contrast-{file.filename or 'image.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }


@router.post(
    "/vision/brightness",
    summary="图片亮度调节",
    description="上传图片后根据亮度偏移值整体提亮或压暗，亮度值范围建议在 -100~100",
)
async def adjust_brightness(
    request: Request,
    file: UploadFile = File(..., description="待处理图片"),
    brightness: float = Form(..., description="亮度偏移值（正值更亮，负值更暗）"),
    save_original: bool = Form(default=False, description="是否保存原图到图库"),
    save_processed: bool = Form(default=True, description="是否保存处理结果到图库"),
    user_id: str | None = Form(default=None, description="当前登录用户 ID"),
) -> dict:
    """根据指定偏移调整图片亮度。"""

    try:
        preview_path, processed_bytes = await process_brightness_image(file, brightness)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="亮度调节失败，请确认文件是否有效") from exc

    processed_image_url = _media_url(request, preview_path)
    saved_original = None
    saved_processed = None

    if user_id and save_original:
        original_path = await save_gallery_upload(file, user_id=user_id)
        original_record = await create_gallery_item(
            user_id=user_id,
            file_url=original_path,
            file_name=file.filename,
        )
        saved_original = _preview_payload(request, original_record)

    if user_id and save_processed:
        processed_path = save_gallery_bytes(
            processed_bytes,
            user_id=user_id,
            suffix=".png",
        )
        processed_record = await create_gallery_item(
            user_id=user_id,
            file_url=processed_path,
            file_name=f"brightness-{file.filename or 'image.png'}",
        )
        saved_processed = _preview_payload(request, processed_record)

    return {
        "processedImage": processed_image_url,
        "savedOriginal": saved_original,
        "savedProcessed": saved_processed,
    }
