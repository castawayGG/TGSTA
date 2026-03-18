"""Main menu keyboards."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Купить Stars"), KeyboardButton(text="📋 Мои заказы")],
            [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="📄 Правила / Оферта")],
        ],
        resize_keyboard=True,
    )


def packages_keyboard(packages: list) -> InlineKeyboardMarkup:
    """Build an inline keyboard for package selection."""
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{p.label} — {p.price_rub()}",
                callback_data=f"pkg:{i}",
            )
        ]
        for i, p in enumerate(packages)
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def recipient_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Я — получатель", callback_data="recipient:self")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="order:cancel_pending")],
        ]
    )


def pay_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отменить заказ",
                    callback_data=f"order:cancel:{order_id}",
                )
            ],
        ]
    )
