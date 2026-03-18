"""Buy flow keyboards."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.config import Package


def packages_keyboard(packages: list[Package]) -> InlineKeyboardMarkup:
    buttons = []
    for i, pkg in enumerate(packages):
        label = f"⭐ {pkg.stars} Stars — {pkg.price_rub} ₽"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"pkg:{i}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="buy:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def confirm_username_keyboard(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Подтвердить @{username}", callback_data=f"confirm_user:{username}")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="change_user")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="buy:cancel")],
        ]
    )


def self_or_other_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Себе", callback_data="recipient:self")],
            [InlineKeyboardButton(text="🔗 Другому пользователю", callback_data="recipient:other")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="buy:cancel")],
        ]
    )
