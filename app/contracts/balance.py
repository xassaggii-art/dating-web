from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance_kopecks: int
    balance_rubles: float


class TopUpPreviewRequest(BaseModel):
    amount_rubles: int = Field(ge=100, le=100000, description="Сумма пополнения в рублях")


class TopUpPreviewResponse(BaseModel):
    amount_kopecks: int
    amount_rubles: float
    new_balance_kopecks: int
    new_balance_rubles: float
    preview_mode: bool
    message: str
