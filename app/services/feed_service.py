from datetime import date
from uuid import UUID

from sqlalchemy import func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.feed import FeedCardDTO, FeedResponse
from app.guards.auth_guard import CurrentActor
from app.infra.database import User, VideoProfileStatus
from app.services.profile_service import ProfileService


def _visible_users_filter():
    return (
        User.deleted_at.is_(None),
        User.profile_frozen.is_(False),
    )


class FeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_cards(
        self,
        actor: CurrentActor,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> FeedResponse:
        query = (
            select(User)
            .where(
                User.is_registered.is_(True),
                User.video_profile_status == VideoProfileStatus.APPROVED,
                User.video_profile_url.isnot(None),
                User.id != actor.id,
                *_visible_users_filter(),
            )
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        if actor.gender == "male":
            query = query.where(User.gender == "female")
        elif actor.gender == "female":
            query = query.where(User.gender == "male")

        if actor.age is not None:
            youngest = actor.age - 5
            oldest = actor.age + 5
            query = query.where(
                User.birth_date.isnot(None),
                User.birth_date >= self._max_birth_date(oldest),
                User.birth_date <= self._min_birth_date(youngest),
            )

        result = await self._session.execute(query)
        users = result.scalars().all()

        cards = [
            FeedCardDTO(
                user_id=u.id,
                name=u.name or "Unknown",
                age=ProfileService.calc_age(u.birth_date) or 0,
                city=u.city,
                avatar_url=u.avatar_url,
                video_profile_url=u.video_profile_url,
                description=ProfileService.truncate_description(u.description),
                attractiveness_score=u.attractiveness_score,
                compatibility_percent=u.compatibility_cache,
            )
            for u in users
        ]
        return FeedResponse(cards=cards)

    async def get_reels(
        self,
        actor: CurrentActor,
        *,
        exclude_ids: list[UUID] | None = None,
        limit: int = 20,
    ) -> FeedResponse:
        query = (
            select(User)
            .where(
                User.is_registered.is_(True),
                User.video_profile_status == VideoProfileStatus.APPROVED,
                User.video_profile_url.isnot(None),
                User.id != actor.id,
                *_visible_users_filter(),
            )
            .order_by(func.random())
            .limit(limit)
        )

        if exclude_ids:
            query = query.where(not_(User.id.in_(exclude_ids)))

        result = await self._session.execute(query)
        users = result.scalars().all()

        cards = [
            FeedCardDTO(
                user_id=u.id,
                name=u.name or "Unknown",
                age=ProfileService.calc_age(u.birth_date) or 0,
                city=u.city,
                avatar_url=u.avatar_url,
                video_profile_url=u.video_profile_url,
                description=ProfileService.truncate_description(u.description),
            )
            for u in users
        ]
        return FeedResponse(cards=cards)

    @staticmethod
    def _max_birth_date(age: int) -> date:
        return date(date.today().year - age, 12, 31)

    @staticmethod
    def _min_birth_date(age: int) -> date:
        return date(date.today().year - age, 1, 1)
