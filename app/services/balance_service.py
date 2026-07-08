from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.contracts.balance import BalanceResponse, TopUpPreviewRequest, TopUpPreviewResponse
from app.infra.database import User


class BalanceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_balance(self, user_id: UUID) -> BalanceResponse:
        user = await self._session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return BalanceResponse(
            balance_kopecks=user.balance,
            balance_rubles=user.balance / 100,
        )

    async def topup_preview(self, user_id: UUID, dto: TopUpPreviewRequest) -> TopUpPreviewResponse:
        settings = get_settings()
        if not settings.debug:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Платёжный шлюз подключается. Пополнение временно недоступно.",
            )

        user = await self._session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        amount_kopecks = dto.amount_rubles * 100
        user.balance += amount_kopecks
        await self._session.commit()
        await self._session.refresh(user)

        return TopUpPreviewResponse(
            amount_kopecks=amount_kopecks,
            amount_rubles=dto.amount_rubles,
            new_balance_kopecks=user.balance,
            new_balance_rubles=user.balance / 100,
            preview_mode=True,
            message="Тестовое пополнение (режим разработки). В продакшене будет подключён платёжный шлюз.",
        )
