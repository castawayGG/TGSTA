"""SQLAlchemy 2.0 async engine, session factory, and Base declarative."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _get_engine_kwargs() -> dict:
    url = settings.database_url
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


# Ensure the data directory exists for SQLite
if settings.database_url.startswith("sqlite"):
    os.makedirs("data", exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    **_get_engine_kwargs(),
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency-style async session generator."""
    async with async_session_factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables (used as fallback when Alembic is not run)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
