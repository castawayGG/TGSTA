"""Main bot entry point."""
from __future__ import annotations

import asyncio
import logging
import os

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.db.base import Base
from bot.db.engine import get_engine
from bot.handlers import admin, buy, help, orders, payment, start
from bot.middlewares.db import DbSessionMiddleware

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(level=logging.INFO)

log = structlog.get_logger()


async def on_startup(bot: Bot) -> None:
    """Initialize DB tables."""
    os.makedirs("data", exist_ok=True)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database_initialized")


async def main() -> None:
    settings = get_settings()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    db_middleware = DbSessionMiddleware()
    dp.message.middleware(db_middleware)
    dp.callback_query.middleware(db_middleware)
    dp.pre_checkout_query.middleware(db_middleware)

    # Routers
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(buy.router)
    dp.include_router(orders.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    dp.startup.register(lambda: on_startup(bot))

    log.info("bot_starting", bot_token_prefix=settings.BOT_TOKEN[:10])

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
