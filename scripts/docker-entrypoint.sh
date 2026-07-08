#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings

async def check() -> None:
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__('sqlalchemy').text('SELECT 1'))
    finally:
        await engine.dispose()

asyncio.run(check())
" 2>/dev/null; do
  sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
