"""Bot entry point."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database import create_all_tables
from app.handlers import admin, common, orders, payments, purchase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting TGSTA bot…")

    # Ensure tables exist (fallback if Alembic is not run)
    await create_all_tables()
    logger.info("Database tables ready.")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers (order matters: payments before purchase for pre_checkout)
    dp.include_router(payments.router)
    dp.include_router(common.router)
    dp.include_router(purchase.router)
    dp.include_router(orders.router)
    dp.include_router(admin.router)

    logger.info("Starting long-polling…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
