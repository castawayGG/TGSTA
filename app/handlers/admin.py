"""Admin panel handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.keyboards.admin import admin_back_keyboard, order_actions_keyboard
from app.models import Order, OrderStatus

logger = logging.getLogger(__name__)

router = Router()

QUEUE_STATUSES = (OrderStatus.paid, OrderStatus.processing, OrderStatus.needs_info)
PAGE_SIZE = 10


class AdminState(StatesGroup):
    waiting_cancel_reason = State()
    waiting_info_message = State()


def _admin_only(user_id: int) -> bool:
    return settings.is_admin(user_id)


# ── /admin command ─────────────────────────────────────────────────────────────


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _admin_only(message.from_user.id):  # type: ignore[union-attr]
        await message.answer("⛔ Доступ запрещён.")
        return
    await _show_queue(message)


# ── Queue listing ─────────────────────────────────────────────────────────────


async def _show_queue(message: Message) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Order)
            .where(Order.status.in_(QUEUE_STATUSES))
            .order_by(Order.created_at.asc())
            .limit(PAGE_SIZE)
        )
        orders = result.scalars().all()

    if not orders:
        await message.answer("✅ Очередь заказов пуста.")
        return

    await message.answer(
        f"📋 <b>Очередь заказов</b> ({len(orders)} шт.):\n\n"
        "Нажмите на номер заказа для управления.",
        parse_mode="HTML",
    )
    for order in orders:
        created = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"
        text = (
            f"{order.status_emoji} <b>Заказ #{order.id}</b>  [{order.status.value}]\n"
            f"📦 {order.package_label}  💰 {order.price_rub}\n"
            f"👤 @{order.recipient_username or '—'}  🆔 user:{order.user_id}\n"
            f"📅 {created}"
            + (f"\n💬 {order.admin_comment}" if order.admin_comment else "")
        )
        await message.answer(text, reply_markup=order_actions_keyboard(order.id), parse_mode="HTML")


# ── Callback: refresh queue ────────────────────────────────────────────────────


@router.callback_query(F.data == "admin:queue")
async def cb_queue(callback: CallbackQuery) -> None:
    if not _admin_only(callback.from_user.id):  # type: ignore[union-attr]
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    await callback.answer()
    await _show_queue(callback.message)  # type: ignore[arg-type]


# ── Status transitions ─────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:processing:"))
async def cb_processing(callback: CallbackQuery) -> None:
    await _transition(callback, OrderStatus.processing, "📌 Заказ взят в обработку.")


@router.callback_query(F.data.startswith("admin:done:"))
async def cb_done(callback: CallbackQuery) -> None:
    await _transition(callback, OrderStatus.done, "✅ Заказ исполнен.")


# ── Cancel with optional reason ────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:cancel:"))
async def cb_cancel_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback.from_user.id):  # type: ignore[union-attr]
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    await state.update_data(order_id=order_id)
    await state.set_state(AdminState.waiting_cancel_reason)
    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        f"❌ Отмена заказа #{order_id}.\n\nВведите причину (или «-» чтобы пропустить):"
    )


@router.message(AdminState.waiting_cancel_reason)
async def cb_cancel_reason(message: Message, state: FSMContext) -> None:
    if not _admin_only(message.from_user.id):  # type: ignore[union-attr]
        return
    data = await state.get_data()
    order_id = data["order_id"]
    reason = message.text.strip() if message.text else ""
    if reason == "-":
        reason = ""
    await state.clear()

    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if not order:
            await message.answer("Заказ не найден.")
            return
        order.status = OrderStatus.canceled
        order.admin_comment = reason or None
        await session.commit()

    await message.answer(f"❌ Заказ #{order_id} отменён.", reply_markup=admin_back_keyboard())
    await _notify_user(
        message,
        order.user_id,
        f"❌ Ваш заказ #{order_id} отменён."
        + (f"\nПричина: {reason}" if reason else ""),
    )


# ── Needs info ────────────────────────────────────────────────────────────────


@router.callback_query(F.data.startswith("admin:needs_info:"))
async def cb_needs_info_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not _admin_only(callback.from_user.id):  # type: ignore[union-attr]
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return
    order_id = int(callback.data.split(":")[2])
    await state.update_data(order_id=order_id)
    await state.set_state(AdminState.waiting_info_message)
    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        f"💬 Сообщение пользователю по заказу #{order_id}.\n\nВведите текст запроса:"
    )


@router.message(AdminState.waiting_info_message)
async def cb_needs_info_text(message: Message, state: FSMContext) -> None:
    if not _admin_only(message.from_user.id):  # type: ignore[union-attr]
        return
    data = await state.get_data()
    order_id = data["order_id"]
    text = message.text or ""
    await state.clear()

    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if not order:
            await message.answer("Заказ не найден.")
            return
        order.status = OrderStatus.needs_info
        order.admin_comment = text
        await session.commit()

    await message.answer(
        f"💬 Запрос отправлен пользователю по заказу #{order_id}.",
        reply_markup=admin_back_keyboard(),
    )
    await _notify_user(
        message,
        order.user_id,
        f"❓ По вашему заказу #{order_id} требуется уточнение:\n\n{text}",
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _transition(callback: CallbackQuery, new_status: OrderStatus, admin_msg: str) -> None:
    if not _admin_only(callback.from_user.id):  # type: ignore[union-attr]
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    order_id = int(callback.data.split(":")[2])

    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if not order:
            await callback.answer("Заказ не найден.", show_alert=True)
            return
        order.status = new_status
        await session.commit()

    await callback.answer(admin_msg)
    try:
        await callback.message.edit_reply_markup(reply_markup=order_actions_keyboard(order_id))  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        logger.debug("Could not update reply markup for order %s", order_id, exc_info=True)

    user_messages = {
        OrderStatus.processing: f"📌 Ваш заказ #{order_id} взят в обработку. Ждите!",
        OrderStatus.done: f"✅ Ваш заказ #{order_id} исполнен! Проверьте баланс Stars.",
    }
    user_text = user_messages.get(new_status)
    if user_text:
        await _notify_user(callback.message, order.user_id, user_text)  # type: ignore[arg-type]


async def _notify_user(source: Message, user_id: int, text: str) -> None:
    try:
        await source.bot.send_message(chat_id=user_id, text=text)  # type: ignore[union-attr]
    except Exception:  # noqa: BLE001
        logger.warning("Could not notify user %s", user_id, exc_info=True)
