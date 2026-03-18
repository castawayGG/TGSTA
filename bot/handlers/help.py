"""Help and rules handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.main import MAIN_MENU

router = Router()

HELP_TEXT = (
    "❓ <b>Помощь</b>\n\n"
    "Этот бот позволяет оформить заявку на пополнение Telegram Stars.\n\n"
    "<b>Как это работает:</b>\n"
    "1. Выберите пакет Stars\n"
    "2. Укажите получателя (себя или другого пользователя)\n"
    "3. Оплатите заказ через Telegram\n"
    "4. Оператор вручную выполнит пополнение в течение SLA\n\n"
    "<b>По всем вопросам:</b> обратитесь к администратору бота."
)

RULES_TEXT = (
    "📜 <b>Правила / Публичная оферта</b>\n\n"
    "1. Сервис предоставляет услугу содействия в пополнении Telegram Stars.\n"
    "2. Исполнение заявок производится оператором вручную. "
    "Срок исполнения указан в описании заказа.\n"
    "3. Оплата производится в рублях через Telegram Payments.\n"
    "4. После оплаты возврат возможен только до момента исполнения заявки. "
    "Для возврата обратитесь к администратору.\n"
    "5. Сервис не несёт ответственности за технические сбои на стороне Telegram.\n"
    "6. Используя сервис, вы соглашаетесь с данными правилами.\n\n"
    "По всем вопросам обращайтесь к администратору."
)


@router.message(F.text == "❓ Помощь")
async def help_handler(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=MAIN_MENU)


@router.message(F.text == "📜 Правила / Оферта")
async def rules_handler(message: Message) -> None:
    await message.answer(RULES_TEXT, parse_mode="HTML", reply_markup=MAIN_MENU)
