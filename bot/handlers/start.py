"""Start and main menu handlers."""
from __future__ import annotations

import structlog
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud import get_or_create_user
from bot.keyboards.main import MAIN_MENU

log = structlog.get_logger()
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    if user:
        await get_or_create_user(
            session,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )
        log.info("user_start", user_id=user.id, username=user.username)

    await message.answer(
        "👋 Добро пожаловать в сервис пополнения Telegram Stars!\n\n"
        "Здесь вы можете оформить заявку на пополнение Stars.\n"
        "⚠️ <b>Важно:</b> исполнение заявок осуществляется оператором вручную "
        "в рабочее время.\n\n"
        "Выберите действие:",
        reply_markup=MAIN_MENU,
        parse_mode="HTML",
    )
