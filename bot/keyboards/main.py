"""Main menu keyboard."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⭐ Купить Stars"), KeyboardButton(text="📋 Мои заказы")],
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="📜 Правила / Оферта")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)
