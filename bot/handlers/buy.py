"""Buy flow handlers."""
from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, LabeledPrice, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.db.crud import create_order, get_or_create_user, update_order_status
from bot.db.models import OrderStatus
from bot.keyboards.buy import (
    cancel_keyboard,
    confirm_username_keyboard,
    packages_keyboard,
    self_or_other_keyboard,
)
from bot.keyboards.main import MAIN_MENU
from bot.states import BuyStates
from bot.utils.validators import normalize_username

log = structlog.get_logger()
router = Router()


@router.message(F.text == "⭐ Купить Stars")
async def buy_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    settings = get_settings()
    packages = settings.get_packages()
    await state.set_state(BuyStates.choosing_package)
    await message.answer(
        "⭐ <b>Купить Telegram Stars</b>\n\n"
        "Выберите пакет Stars для пополнения:\n\n"
        "⚠️ <i>Исполнение заявок — ручное, оператором. "
        "Срок указывается после оплаты.</i>",
        reply_markup=packages_keyboard(packages),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "buy:cancel")
async def buy_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Покупка отменена.")  # type: ignore[union-attr]
    await callback.message.answer("Главное меню:", reply_markup=MAIN_MENU)  # type: ignore[union-attr]
    await callback.answer()


@router.message(BuyStates.entering_username, F.text == "❌ Отмена")
async def buy_cancel_via_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Покупка отменена.", reply_markup=MAIN_MENU)


@router.callback_query(F.data.startswith("pkg:"), BuyStates.choosing_package)
async def package_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    settings = get_settings()
    packages = settings.get_packages()
    idx_str = callback.data.split(":")[1]  # type: ignore[union-attr]
    try:
        idx = int(idx_str)
        pkg = packages[idx]
    except (ValueError, IndexError):
        await callback.answer("Неверный выбор.", show_alert=True)
        return

    user = callback.from_user
    await get_or_create_user(
        session,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

    # Create order in DB at "created" status
    order = await create_order(
        session,
        user_id=user.id,
        stars=pkg.stars,
        price_rub=pkg.price_rub * 100,  # store in kopecks
    )
    await update_order_status(session, order.id, OrderStatus.awaiting_username)

    await state.update_data(order_id=order.id, pkg_idx=idx, stars=pkg.stars, price_rub=pkg.price_rub)
    await state.set_state(BuyStates.choosing_recipient)

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"✅ Выбрано: <b>⭐ {pkg.stars} Stars</b> за <b>{pkg.price_rub} ₽</b>\n\n"
        "Кому пополнить Stars?",
        reply_markup=self_or_other_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "recipient:self", BuyStates.choosing_recipient)
async def recipient_self(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    if not user.username:
        await callback.answer(
            "У вас не установлен @username в Telegram. "
            "Установите его в настройках и попробуйте снова.",
            show_alert=True,
        )
        return

    await state.update_data(recipient_username=user.username)
    await state.set_state(BuyStates.confirming_username)

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"Получатель: <b>@{user.username}</b> (вы)\n\nПодтвердите выбор:",
        reply_markup=confirm_username_keyboard(user.username),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "recipient:other", BuyStates.choosing_recipient)
async def recipient_other(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BuyStates.entering_username)
    await callback.message.edit_text(  # type: ignore[union-attr]
        "Введите @username получателя:\n\n"
        "<i>Формат: @username или username или t.me/username</i>",
        parse_mode="HTML",
    )
    await callback.message.answer(  # type: ignore[union-attr]
        "Введите @username:", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(BuyStates.entering_username)
async def username_entered(message: Message, state: FSMContext) -> None:
    raw = message.text or ""
    username = normalize_username(raw)
    if not username:
        await message.answer(
            "❌ Неверный формат username.\n\n"
            "Допустимые форматы: @username, username, t.me/username\n"
            "Username должен содержать 5–32 символа (латиница, цифры, _).\n\n"
            "Попробуйте ещё раз:",
            reply_markup=cancel_keyboard(),
        )
        return

    await state.update_data(recipient_username=username)
    await state.set_state(BuyStates.confirming_username)
    await message.answer(
        f"Получатель: <b>@{username}</b>\n\nПодтвердите выбор:",
        reply_markup=confirm_username_keyboard(username),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "change_user", BuyStates.confirming_username)
async def change_username(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BuyStates.entering_username)
    await callback.message.edit_text(  # type: ignore[union-attr]
        "Введите @username получателя:",
        parse_mode="HTML",
    )
    await callback.message.answer(  # type: ignore[union-attr]
        "Введите @username:", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_user:"), BuyStates.confirming_username)
async def username_confirmed(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    order_id: int = data["order_id"]
    stars: int = data["stars"]
    price_rub: int = data["price_rub"]
    recipient_username: str = data.get("recipient_username", "")

    settings = get_settings()

    # Update order with recipient username and move to invoice_sent
    from bot.db.crud import get_order

    order = await get_order(session, order_id)
    if order is None:
        await callback.answer("Ошибка: заказ не найден.", show_alert=True)
        await state.clear()
        return

    order.recipient_username = recipient_username
    order.status = OrderStatus.invoice_sent

    title = f"⭐ {stars} Telegram Stars"
    description = (
        f"Пополнение Telegram Stars для @{recipient_username}. "
        "Исполнение заявки — вручную оператором."
    )
    payload = f"order:{order_id}"
    prices = [LabeledPrice(label=title, amount=price_rub * 100)]  # amount in kopecks

    await callback.message.answer_invoice(  # type: ignore[union-attr]
        title=title,
        description=description,
        payload=payload,
        provider_token=settings.PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter=f"order{order_id}",
        protect_content=False,
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📨 Счёт на оплату выставлен!\n\n"
        f"⭐ <b>{stars} Stars</b> для @{recipient_username}\n"
        f"Сумма: <b>{price_rub} ₽</b>\n\n"
        f"Оплатите счёт выше для подтверждения заказа.",
        parse_mode="HTML",
    )
    await state.clear()
    await callback.answer()
    log.info("invoice_sent", order_id=order_id, user_id=callback.from_user.id, stars=stars)
