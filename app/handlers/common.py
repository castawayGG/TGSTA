"""Common handlers: /start, /help, menu text buttons."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.database import async_session_factory
from app.keyboards.main_menu import main_menu
from app.models import User

router = Router()


async def _upsert_user(tg_user) -> None:  # type: ignore[no-untyped-def]
    """Insert or update a User record."""
    async with async_session_factory() as session:
        user = await session.get(User, tg_user.id)
        if user is None:
            user = User(
                id=tg_user.id,
                username=tg_user.username,
                full_name=tg_user.full_name,
            )
            session.add(user)
        else:
            user.username = tg_user.username
            user.full_name = tg_user.full_name
        await session.commit()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if message.from_user:
        await _upsert_user(message.from_user)
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Этот бот позволяет заказать пополнение Telegram Stars за рубли.\n\n"
        "<i>Исполнение — вручную администратором. "
        f"{settings.order_sla_text}</i>\n\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu(),
        parse_mode="HTML",
    )


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "• <b>⭐ Купить Stars</b> — выбрать пакет и оплатить.\n"
        "• <b>📋 Мои заказы</b> — история ваших заказов.\n"
        "• <b>📄 Правила / Оферта</b> — условия сервиса.\n\n"
        f"Поддержка: {settings.support_contact}",
        parse_mode="HTML",
    )


@router.message(F.text == "📄 Правила / Оферта")
async def cmd_terms(message: Message) -> None:
    text = settings.effective_terms
    await message.answer(
        f"📄 <b>Правила / Оферта</b>\n\n{text}",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
