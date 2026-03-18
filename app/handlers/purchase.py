"""Purchase flow: package selection → recipient → invoice."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
)

from app.config import settings
from app.database import async_session_factory
from app.keyboards.main_menu import packages_keyboard, pay_keyboard, recipient_keyboard
from app.models import Order, OrderStatus, User
from app.utils.validators import normalize_username, validate_username

router = Router()


class PurchaseState(StatesGroup):
    choosing_package = State()
    entering_recipient = State()
    awaiting_payment = State()


# ── Trigger from menu button ──────────────────────────────────────────────────


@router.message(F.text == "⭐ Купить Stars")
async def buy_stars_menu(message: Message, state: FSMContext) -> None:
    packages = settings.get_packages()
    await state.set_state(PurchaseState.choosing_package)
    await message.answer(
        "⭐ <b>Выберите пакет Stars:</b>\n\n"
        "<i>После оплаты укажите @username получателя. "
        f"{settings.order_sla_text}</i>",
        reply_markup=packages_keyboard(packages),
        parse_mode="HTML",
    )


# ── Package selection ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("pkg:"))
async def choose_package(callback: CallbackQuery, state: FSMContext) -> None:
    packages = settings.get_packages()
    idx = int(callback.data.split(":")[1])
    if idx >= len(packages):
        await callback.answer("Пакет не найден.", show_alert=True)
        return

    pkg = packages[idx]
    await state.update_data(pkg_idx=idx, stars=pkg.stars, price=pkg.price, label=pkg.label)
    await state.set_state(PurchaseState.entering_recipient)

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📦 Выбран пакет: <b>{pkg.label}</b> за <b>{pkg.price_rub()}</b>\n\n"
        "Укажите <b>@username</b> получателя (кому зачислять Stars)\n"
        "или нажмите кнопку ниже, если получатель — вы:",
        reply_markup=recipient_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Recipient: "I am the recipient" ──────────────────────────────────────────


@router.callback_query(F.data == "recipient:self")
async def recipient_self(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    username = f"@{user.username}" if user and user.username else None
    if not username:
        await callback.answer(
            "У вашего аккаунта нет @username. Введите username получателя вручную.",
            show_alert=True,
        )
        return
    await _create_order_and_invoice(callback, state, username)


# ── Recipient: typed @username ────────────────────────────────────────────────


@router.message(PurchaseState.entering_recipient)
async def recipient_typed(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not validate_username(text):
        await message.answer(
            "⚠️ Некорректный @username. Введите корректный username "
            "(5–32 символа, буквы/цифры/подчёркивание):"
        )
        return
    await _create_order_and_invoice_msg(message, state, text)


# ── Cancel pending order (before payment) ─────────────────────────────────────


@router.callback_query(F.data == "order:cancel_pending")
async def cancel_pending(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")
    if order_id:
        async with async_session_factory() as session:
            order = await session.get(Order, order_id)
            cancelable = (
                OrderStatus.created,
                OrderStatus.awaiting_username,
                OrderStatus.awaiting_payment,
            )
            if order and order.status in cancelable:
                order.status = OrderStatus.canceled
                await session.commit()
    await state.clear()
    await callback.message.edit_text("❌ Заказ отменён.")  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data.startswith("order:cancel:"))
async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if order and order.status == OrderStatus.awaiting_payment:
            if order.user_id == callback.from_user.id:  # type: ignore[union-attr]
                order.status = OrderStatus.canceled
                await session.commit()
                await callback.message.edit_text("❌ Заказ отменён.")  # type: ignore[union-attr]
                await state.clear()
                await callback.answer()
                return
    await callback.answer("Невозможно отменить этот заказ.", show_alert=True)


# ── Back to main menu ─────────────────────────────────────────────────────────


@router.callback_query(F.data == "menu:main")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Главное меню.")  # type: ignore[union-attr]
    await callback.answer()


# ── Internal helpers ──────────────────────────────────────────────────────────


async def _create_order_and_invoice(
    callback: CallbackQuery,
    state: FSMContext,
    recipient: str,
) -> None:
    data = await state.get_data()
    order = await _persist_order(callback.from_user.id, data, recipient)  # type: ignore[union-attr]
    await state.update_data(order_id=order.id)
    await state.set_state(PurchaseState.awaiting_payment)

    await callback.message.edit_text(  # type: ignore[union-attr]
        f"📦 Пакет: <b>{order.package_label}</b>\n"
        f"👤 Получатель: <code>{recipient}</code>\n"
        f"💰 Сумма: <b>{order.price_rub}</b>\n\n"
        "Отправляю счёт на оплату…",
        parse_mode="HTML",
    )
    await callback.answer()

    await _send_invoice(callback.message.chat.id, order, callback.bot)  # type: ignore[union-attr]


async def _create_order_and_invoice_msg(
    message: Message,
    state: FSMContext,
    recipient: str,
) -> None:
    data = await state.get_data()
    order = await _persist_order(message.from_user.id, data, recipient)  # type: ignore[union-attr]
    await state.update_data(order_id=order.id)
    await state.set_state(PurchaseState.awaiting_payment)

    await message.answer(
        f"📦 Пакет: <b>{order.package_label}</b>\n"
        f"👤 Получатель: <code>{recipient}</code>\n"
        f"💰 Сумма: <b>{order.price_rub}</b>\n\n"
        "Отправляю счёт на оплату…",
        parse_mode="HTML",
    )
    await _send_invoice(message.chat.id, order, message.bot)  # type: ignore[union-attr]


async def _persist_order(user_id: int, data: dict, recipient: str) -> Order:
    async with async_session_factory() as session:
        # Ensure user exists
        user = await session.get(User, user_id)
        if user is None:
            user = User(id=user_id)
            session.add(user)

        order = Order(
            user_id=user_id,
            stars=data["stars"],
            price=data["price"],
            currency=settings.currency,
            package_label=data["label"],
            recipient_username=normalize_username(recipient),
            status=OrderStatus.awaiting_payment,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


async def _send_invoice(chat_id: int, order: Order, bot) -> None:  # type: ignore[no-untyped-def]
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"Пополнение Stars: {order.package_label}",
        description=(
            f"Пополнение {order.stars} Telegram Stars для @{order.recipient_username}.\n"
            f"Заказ #{order.id}. {settings.order_sla_text}"
        ),
        payload=f"order:{order.id}",
        provider_token=settings.provider_token,
        currency=settings.currency,
        prices=[LabeledPrice(label=order.package_label, amount=order.price)],
        reply_markup=pay_keyboard(order.id),
    )
