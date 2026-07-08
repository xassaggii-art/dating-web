from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.infra.database import async_session_factory, init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routes import auth, balance, basket, chats, config, feed, interaction, pricing, profile, support

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    await init_db()
    if settings.debug:
        from app.services.seed_service import seed_demo_users

        async with async_session_factory() as session:
            created = await seed_demo_users(session)
            if created:
                print(f"Seeded {created} demo users (login: anna@demo.local / demo12345)")
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Guest-UUID", "X-2FA-Code"],
    )

    prefix = settings.api_prefix
    app.include_router(auth.router, prefix=prefix)
    app.include_router(feed.router, prefix=prefix)
    app.include_router(interaction.router, prefix=prefix)
    app.include_router(basket.router, prefix=prefix)
    app.include_router(chats.router, prefix=prefix)
    app.include_router(pricing.router, prefix=prefix)
    app.include_router(balance.router, prefix=prefix)
    app.include_router(profile.router, prefix=prefix)
    app.include_router(config.router, prefix=prefix)
    app.include_router(support.router, prefix=prefix)

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
