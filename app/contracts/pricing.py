from pydantic import BaseModel


class PricingPlanDTO(BaseModel):
    slug: str
    name: str
    pricing_type: str
    duration_minutes: int | None
    price_kopecks: int
    price_rubles: float
    per_minute_rate_kopecks: int | None = None
    min_minutes: int | None = None


class PriceQuoteRequest(BaseModel):
    plan_slug: str
    minutes: int | None = None


class PriceQuoteResponse(BaseModel):
    plan_slug: str
    pricing_type: str
    duration_minutes: int
    price_kopecks: int
    price_rubles: float
    per_minute_rate_kopecks: int | None = None
