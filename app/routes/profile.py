from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.profile import (
    AvatarConfirmRequest,
    AvatarUploadUrlRequest,
    ProfileResponse,
    ProfileUpdateDTO,
    VideoConfirmRequest,
    VideoQuestionsResponse,
    VideoStatusResponse,
    VideoUploadUrlRequest,
    VideoUploadUrlResponse,
)
from app.guards.auth_guard import CurrentActor, get_current_actor, require_registered
from app.infra.database import get_session
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_response(user, service: ProfileService) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        name=user.name,
        birth_date=user.birth_date.isoformat() if user.birth_date else None,
        city=user.city,
        gender=user.gender,
        avatar_url=user.avatar_url,
        video_profile_url=user.video_profile_url,
        video_status=service.map_video_status(user.video_profile_status),
        description=user.description,
        occupation=user.occupation,
        balance_kopecks=user.balance,
        balance_rubles=user.balance / 100,
        profile_frozen=user.profile_frozen,
        attractiveness_score=user.attractiveness_score,
        overall_rating=user.overall_rating,
    )


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    service = ProfileService(session)
    user = await service.get_profile(actor.id)
    return _profile_response(user, service)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    dto: ProfileUpdateDTO,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    service = ProfileService(session)
    user = await service.update_profile(actor.id, dto)
    return _profile_response(user, service)


@router.post("/avatar/upload-url", response_model=VideoUploadUrlResponse)
async def avatar_upload_url(
    dto: AvatarUploadUrlRequest,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> VideoUploadUrlResponse:
    service = ProfileService(session)
    url, key = await service.create_avatar_upload_url(actor.id, dto.content_type)
    return VideoUploadUrlResponse(upload_url=url, object_key=key)


@router.post("/avatar/confirm", response_model=ProfileResponse)
async def avatar_confirm(
    dto: AvatarConfirmRequest,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    service = ProfileService(session)
    user = await service.confirm_avatar(actor.id, dto.object_key)
    return _profile_response(user, service)


@router.get("/video/questions", response_model=VideoQuestionsResponse)
async def video_questions(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> VideoQuestionsResponse:
    data = ProfileService(session).get_video_questions()
    return VideoQuestionsResponse(**data)


@router.post("/video/upload-url", response_model=VideoUploadUrlResponse)
async def video_upload_url(
    dto: VideoUploadUrlRequest,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> VideoUploadUrlResponse:
    service = ProfileService(session)
    url, key = await service.create_upload_url(actor.id, dto.content_type)
    return VideoUploadUrlResponse(upload_url=url, object_key=key)


@router.post("/video/confirm", response_model=VideoStatusResponse)
async def video_confirm(
    dto: VideoConfirmRequest,
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> VideoStatusResponse:
    service = ProfileService(session)
    await service.confirm_upload(actor.id, dto.object_key)
    return VideoStatusResponse(status="processing")


@router.get("/video/status", response_model=VideoStatusResponse)
async def video_status(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> VideoStatusResponse:
    service = ProfileService(session)
    user = await service.get_profile(actor.id)
    return VideoStatusResponse(
        status=service.map_video_status(user.video_profile_status),
        video_profile_url=user.video_profile_url,
        avatar_url=user.avatar_url,
    )


@router.post("/freeze", response_model=ProfileResponse)
async def freeze_profile(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    service = ProfileService(session)
    user = await service.set_profile_frozen(actor.id, True)
    return _profile_response(user, service)


@router.post("/unfreeze", response_model=ProfileResponse)
async def unfreeze_profile(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    service = ProfileService(session)
    user = await service.set_profile_frozen(actor.id, False)
    return _profile_response(user, service)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    actor: CurrentActor = Depends(require_registered),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await ProfileService(session).soft_delete_profile(actor.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
