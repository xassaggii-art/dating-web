import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.auth import (
    GuestSessionDTO,
    GuestSessionResponse,
    RefreshTokenDTO,
    TokenResponse,
    UserLoginDTO,
    UserRegisterDTO,
)
from app.contracts.security import TwoFactorCodeDTO, TwoFactorSetupResponse, TwoFactorStatusDTO
from app.guards.auth_guard import CurrentActor, get_current_actor
from app.infra.database import get_session
from app.infra.http import get_client_ip, get_user_agent
from app.infra.session import store_guest_session
from app.middleware.rate_limit import rate_limit_login, rate_limit_register
from app.services.auth_service import AuthService
from app.services.two_factor_service import TwoFactorService

router = APIRouter(tags=["auth"])


@router.post("/session/guest", response_model=GuestSessionResponse)
async def create_guest_session(dto: GuestSessionDTO) -> GuestSessionResponse:
    guest_id = uuid.uuid4()
    await store_guest_session(guest_id, dto.gender, dto.age)
    return GuestSessionResponse(guest_session_id=guest_id, gender=dto.gender, age=dto.age)


@router.post("/auth/register", response_model=TokenResponse)
async def register(
    dto: UserRegisterDTO,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit_register),
) -> TokenResponse:
    service = AuthService(session)
    user, access, refresh = await service.register(
        dto,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return TokenResponse(access_token=access, refresh_token=refresh, user_id=user.id)


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    dto: UserLoginDTO,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(rate_limit_login),
) -> TokenResponse:
    service = AuthService(session)
    user, access, refresh, requires_2fa = await service.login(
        dto,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user.id,
        requires_2fa=requires_2fa,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    dto: RefreshTokenDTO,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    service = AuthService(session)
    user, access, new_refresh = await service.refresh(
        dto.refresh_token,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return TokenResponse(access_token=access, refresh_token=new_refresh, user_id=user.id)


@router.post("/auth/logout", status_code=204)
async def logout(
    dto: RefreshTokenDTO,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> None:
    service = AuthService(session)
    await service.logout(
        dto.refresh_token,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.post("/auth/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TwoFactorSetupResponse:
    if actor.is_guest:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration required")
    service = TwoFactorService(session)
    data = await service.setup(actor.id)
    await session.commit()
    return TwoFactorSetupResponse(**data)


@router.post("/auth/2fa/enable", response_model=TwoFactorStatusDTO)
async def enable_2fa(
    dto: TwoFactorCodeDTO,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TwoFactorStatusDTO:
    service = TwoFactorService(session)
    await service.enable(actor.id, dto.code)
    return TwoFactorStatusDTO(enabled=True)


@router.post("/auth/2fa/disable", response_model=TwoFactorStatusDTO)
async def disable_2fa(
    dto: TwoFactorCodeDTO,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> TwoFactorStatusDTO:
    service = TwoFactorService(session)
    await service.disable(actor.id, dto.code)
    return TwoFactorStatusDTO(enabled=False)


@router.get("/auth/2fa/status", response_model=TwoFactorStatusDTO)
async def status_2fa(actor: CurrentActor = Depends(get_current_actor)) -> TwoFactorStatusDTO:
    return TwoFactorStatusDTO(enabled=actor.totp_enabled)
