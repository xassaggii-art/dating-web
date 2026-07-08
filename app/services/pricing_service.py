from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import PricingPlan, PricingType


class PricingService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_active_plans(self) -> list[PricingPlan]:
        result = await self._db.execute(
            select(PricingPlan)
            .where(PricingPlan.is_active.is_(True))
            .order_by(PricingPlan.sort_order)
        )
        return list(result.scalars().all())

    async def calculate_price(self, plan_slug: str, minutes: int | None = None) -> dict:
        result = await self._db.execute(
            select(PricingPlan).where(PricingPlan.slug == plan_slug, PricingPlan.is_active.is_(True))
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise ValueError(f"Unknown pricing plan: {plan_slug}")

        if plan.pricing_type == PricingType.PACKAGE:
            return {
                "plan_slug": plan.slug,
                "pricing_type": plan.pricing_type.value,
                "duration_minutes": plan.duration_minutes,
                "price_kopecks": plan.price_kopecks,
                "price_rubles": plan.price_kopecks / 100,
            }

        if minutes is None:
            minutes = plan.min_minutes or 15
        if plan.min_minutes and minutes < plan.min_minutes:
            minutes = plan.min_minutes
        rate = plan.per_minute_rate_kopecks or 0
        total = rate * minutes
        return {
            "plan_slug": plan.slug,
            "pricing_type": plan.pricing_type.value,
            "duration_minutes": minutes,
            "per_minute_rate_kopecks": rate,
            "price_kopecks": total,
            "price_rubles": total / 100,
        }
