"""个人中心与用户资料路由。"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import UserInfo
from app.schemas.user import UserProfileUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["User"])


@router.get("/{user_id}", response_model=UserInfo, summary="获取个人资料")
async def get_user_profile(
    user_id: str,
    service: UserService = Depends(),
) -> UserInfo:
    try:
        return await service.get_profile(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{user_id}", response_model=UserInfo, summary="更新个人资料")
async def update_user_profile(
    user_id: str,
    payload: UserProfileUpdate,
    service: UserService = Depends(),
) -> UserInfo:
    try:
        return await service.update_profile(user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
