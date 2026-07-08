from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.pricing import PriceQuoteRequest, PriceQuoteResponse, PricingPlanDTO
from app.infra.database import get_session
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/plans", response_model=list[PricingPlanDTO])
async def list_plans(session: AsyncSession = Depends(get_session)) -> list[PricingPlanDTO]:
    service = PricingService(session)
    plans = await service.list_active_plans()
    return [
        PricingPlanDTO(
            slug=p.slug,
            name=p.name,
            pricing_type=p.pricing_type.value,
            duration_minutes=p.duration_minutes,
            price_kopecks=p.price_kopecks,
            price_rubles=p.price_kopecks / 100,
            per_minute_rate_kopecks=p.per_minute_rate_kopecks,
            min_minutes=p.min_minutes,
        )
        for p in plans
    ]


@router.post("/quote", response_model=PriceQuoteResponse)
async def quote_price(
    dto: PriceQuoteRequest,
    session: AsyncSession = Depends(get_session),
) -> PriceQuoteResponse:
    service = PricingService(session)
    try:
        result = await service.calculate_price(dto.plan_slug, dto.minutes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PriceQuoteResponse(
        plan_slug=result["plan_slug"],
        pricing_type=result["pricing_type"],
        duration_minutes=result["duration_minutes"],
        price_kopecks=result["price_kopecks"],
        price_rubles=result["price_rubles"],
        per_minute_rate_kopecks=result.get("per_minute_rate_kopecks"),
    )
