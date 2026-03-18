"""Admin keyboards."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.models import Order


def admin_order_keyboard(order: Order) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 В обработку", callback_data=f"adm:processing:{order.id}"),
                InlineKeyboardButton(text="✅ Исполнено", callback_data=f"adm:completed:{order.id}"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена (возврат)", callback_data=f"adm:cancelled:{order.id}"),
                InlineKeyboardButton(text="💬 Уточнение", callback_data=f"adm:clarify:{order.id}"),
            ],
        ]
    )


def admin_queue_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить очередь", callback_data="adm:refresh")],
        ]
    )
