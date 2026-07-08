"""Seed demo users for local preview (debug only)."""

from datetime import date

from sqlalchemy import func, select, update

from app.infra.database import User, VideoProfileStatus
from app.infra.security import hash_password

DEMO_VIDEO = "https://sample-videos.com/video123/mp4/h264/big_buck_bunny_360p_1mb.mp4"
DEMO_EMAILS = ("anna@demo.local", "maria@demo.local", "ivan@demo.local")


async def seed_demo_users(session) -> int:
    count = await session.scalar(select(func.count()).select_from(User))
    if count and count > 0:
        await session.execute(
            update(User)
            .where(User.email.in_(DEMO_EMAILS))
            .values(
                video_profile_url=DEMO_VIDEO,
                video_profile_status=VideoProfileStatus.APPROVED,
                is_registered=True,
            )
        )
        await session.execute(
            update(User)
            .where(User.email == "anna@demo.local", User.description.is_(None))
            .values(description="Люблю путешествия, кино и долгие прогулки")
        )
        await session.execute(
            update(User)
            .where(User.email == "maria@demo.local", User.description.is_(None))
            .values(description="Ищу искренние знакомства и хороший юмор")
        )
        await session.execute(
            update(User)
            .where(User.email == "ivan@demo.local", User.description.is_(None))
            .values(description="Спорт, музыка и новые впечатления каждый день")
        )
        await session.commit()
        return 0

    demos = [
        User(
            name="Анна",
            email="anna@demo.local",
            password_hash=hash_password("demo12345"),
            birth_date=date(1998, 3, 15),
            city="Москва",
            gender="female",
            is_registered=True,
            video_profile_status=VideoProfileStatus.APPROVED,
            avatar_url=None,
            video_profile_url=DEMO_VIDEO,
            description="Люблю путешествия, кино и долгие прогулки",
        ),
        User(
            name="Мария",
            email="maria@demo.local",
            password_hash=hash_password("demo12345"),
            birth_date=date(1996, 7, 22),
            city="Санкт-Петербург",
            gender="female",
            is_registered=True,
            video_profile_status=VideoProfileStatus.APPROVED,
            video_profile_url=DEMO_VIDEO,
            description="Ищу искренние знакомства и хороший юмор",
        ),
        User(
            name="Иван",
            email="ivan@demo.local",
            password_hash=hash_password("demo12345"),
            birth_date=date(1995, 11, 8),
            city="Москва",
            gender="male",
            is_registered=True,
            video_profile_status=VideoProfileStatus.APPROVED,
            video_profile_url=DEMO_VIDEO,
            description="Спорт, музыка и новые впечатления каждый день",
        ),
    ]
    session.add_all(demos)
    await session.commit()
    return len(demos)
