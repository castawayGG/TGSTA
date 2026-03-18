"""Admin panel keyboards."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📌 В обработку",
                    callback_data=f"admin:processing:{order_id}",
                ),
                InlineKeyboardButton(
                    text="✅ Исполнено",
                    callback_data=f"admin:done:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=f"admin:cancel:{order_id}",
                ),
                InlineKeyboardButton(
                    text="💬 Запросить инфо",
                    callback_data=f"admin:needs_info:{order_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 К списку",
                    callback_data="admin:queue",
                ),
            ],
        ]
    )


def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin:queue")]
        ]
    )
