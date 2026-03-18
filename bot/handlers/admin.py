"""Admin panel handlers."""
from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.crud import get_order, get_pending_orders, update_order_status
from bot.db.models import OrderStatus
from bot.keyboards.admin import admin_order_keyboard, admin_queue_keyboard
from bot.keyboards.main import MAIN_MENU
from bot.states import AdminStates

log = structlog.get_logger()
router = Router()


def _format_order(order) -> str:
    recipient = f"@{order.recipient_username}" if order.recipient_username else "не указан"
    return (
        f"📦 <b>Заказ #{order.id}</b>\n"
        f"👤 Пользователь: <code>{order.user_id}</code>\n"
        f"⭐ Stars: {order.stars}\n"
        f"💰 Сумма: {order.price_rub // 100} ₽\n"
        f"📨 Получатель: {recipient}\n"
        f"🔖 Статус: {order.status.value}\n"
        f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession) -> None:
    """Show admin queue."""
    from bot.config import get_settings

    settings = get_settings()
    if message.from_user and message.from_user.id not in settings.get_admin_ids():
        await message.answer("⛔ Доступ запрещён.")
        return

    orders = await get_pending_orders(session)
    if not orders:
        await message.answer(
            "✅ Очередь пуста — нет оплаченных или обрабатываемых заказов.",
            reply_markup=admin_queue_keyboard(),
        )
        return

    await message.answer(
        f"🗂 <b>Очередь заказов</b> ({len(orders)} шт.):",
        parse_mode="HTML",
        reply_markup=admin_queue_keyboard(),
    )
    for order in orders:
        await message.answer(
            _format_order(order),
            parse_mode="HTML",
            reply_markup=admin_order_keyboard(order),
        )

    log.info("admin_queue_viewed", admin_id=message.from_user.id if message.from_user else None, count=len(orders))


@router.callback_query(F.data == "adm:refresh")
async def admin_refresh(callback: CallbackQuery, session: AsyncSession) -> None:
    from bot.config import get_settings

    settings = get_settings()
    if callback.from_user.id not in settings.get_admin_ids():
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    orders = await get_pending_orders(session)
    await callback.answer(f"Обновлено: {len(orders)} заказов в очереди")


@router.callback_query(F.data.startswith("adm:processing:"))
async def set_processing(callback: CallbackQuery, session: AsyncSession) -> None:
    await _change_status(callback, session, OrderStatus.processing, "🔄 Заказ #{id} взят в обработку.")


@router.callback_query(F.data.startswith("adm:completed:"))
async def set_completed(callback: CallbackQuery, session: AsyncSession) -> None:
    await _change_status(callback, session, OrderStatus.completed, "✅ Заказ #{id} исполнен!")


@router.callback_query(F.data.startswith("adm:cancelled:"))
async def set_cancelled(callback: CallbackQuery, session: AsyncSession) -> None:
    await _change_status(
        callback, session, OrderStatus.cancelled,
        "❌ Заказ #{id} отменён. Если вы оплачивали — обратитесь к администратору для возврата."
    )


@router.callback_query(F.data.startswith("adm:clarify:"))
async def request_clarification(callback: CallbackQuery, state: FSMContext) -> None:
    from bot.config import get_settings

    settings = get_settings()
    if callback.from_user.id not in settings.get_admin_ids():
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    order_id_str = callback.data.split(":")[-1]  # type: ignore[union-attr]
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback.answer("Ошибка.", show_alert=True)
        return

    await state.set_state(AdminStates.entering_clarification)
    await state.update_data(clarify_order_id=order_id, clarify_msg_id=callback.message.message_id)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"💬 Введите сообщение для пользователя по заказу #{order_id}:",
    )
    await callback.answer()


@router.message(AdminStates.entering_clarification)
async def clarification_entered(message: Message, state: FSMContext, session: AsyncSession) -> None:
    from bot.config import get_settings

    settings = get_settings()
    if message.from_user and message.from_user.id not in settings.get_admin_ids():
        return

    data = await state.get_data()
    order_id: int = data.get("clarify_order_id", 0)
    note = message.text or ""

    await update_order_status(session, order_id, OrderStatus.clarification_requested, admin_note=note)
    await state.clear()

    order = await get_order(session, order_id)
    if order and message.bot:
        try:
            await message.bot.send_message(
                order.user_id,
                f"💬 <b>По вашему заказу #{order_id} требуется уточнение</b>\n\n"
                f"{note}\n\n"
                "Пожалуйста, свяжитесь с администратором.",
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("clarify_notify_failed", user_id=order.user_id, error=str(e))

    await message.answer(
        f"✅ Сообщение отправлено пользователю по заказу #{order_id}.",
        reply_markup=MAIN_MENU,
    )
    log.info("clarification_sent", order_id=order_id, admin_id=message.from_user.id if message.from_user else None)


async def _change_status(
    callback: CallbackQuery,
    session: AsyncSession,
    new_status: OrderStatus,
    user_message_template: str,
) -> None:
    from bot.config import get_settings

    settings = get_settings()
    if callback.from_user.id not in settings.get_admin_ids():
        await callback.answer("⛔ Доступ запрещён.", show_alert=True)
        return

    order_id_str = callback.data.split(":")[-1]  # type: ignore[union-attr]
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback.answer("Ошибка.", show_alert=True)
        return

    order = await update_order_status(session, order_id, new_status)
    if order is None:
        await callback.answer("Заказ не найден.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer(f"Статус изменён: {new_status.value}")
    log.info("order_status_changed", order_id=order_id, new_status=new_status.value)

    # Notify user
    user_msg = user_message_template.format(id=order_id)
    if callback.bot:
        try:
            await callback.bot.send_message(
                order.user_id,
                f"🔔 <b>Обновление заказа #{order_id}</b>\n\n{user_msg}",
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning("user_notify_failed", user_id=order.user_id, error=str(e))
