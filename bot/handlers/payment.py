"""Payment handlers: pre_checkout_query and successful_payment."""
from __future__ import annotations

import structlog
from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.db.crud import get_order, get_order_by_charge_id, mark_order_paid
from bot.db.models import OrderStatus
from bot.keyboards.main import MAIN_MENU

log = structlog.get_logger()
router = Router()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery, session: AsyncSession) -> None:
    """Validate order before payment."""
    payload = query.invoice_payload
    if not payload.startswith("order:"):
        await query.answer(ok=False, error_message="Неверный платёж.")
        return

    try:
        order_id = int(payload.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(ok=False, error_message="Неверный платёж.")
        return

    order = await get_order(session, order_id)
    if order is None:
        await query.answer(ok=False, error_message="Заказ не найден.")
        return

    if order.status not in (OrderStatus.invoice_sent, OrderStatus.awaiting_username):
        # Idempotency: already paid
        if order.status == OrderStatus.paid:
            await query.answer(ok=True)
            return
        await query.answer(ok=False, error_message="Заказ уже обработан или отменён.")
        return

    await query.answer(ok=True)
    log.info("pre_checkout_ok", order_id=order_id, user_id=query.from_user.id)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment_handler(message: Message, session: AsyncSession) -> None:
    """Handle successful payment."""
    payment = message.successful_payment
    if not payment:
        return

    payload = payment.invoice_payload
    telegram_charge_id = payment.telegram_payment_charge_id
    provider_charge_id = payment.provider_payment_charge_id

    # Idempotency: check by telegram_payment_charge_id
    existing = await get_order_by_charge_id(session, telegram_charge_id)
    if existing is not None:
        log.warning("duplicate_payment", charge_id=telegram_charge_id)
        await message.answer(
            f"ℹ️ Этот платёж уже зарегистрирован (заказ #{existing.id}).",
            reply_markup=MAIN_MENU,
        )
        return

    try:
        order_id = int(payload.split(":")[1])
    except (ValueError, IndexError):
        log.error("bad_payload", payload=payload)
        return

    order = await get_order(session, order_id)
    if order is None:
        log.error("order_not_found_on_payment", order_id=order_id)
        return

    order = await mark_order_paid(
        session,
        order_id=order_id,
        telegram_payment_charge_id=telegram_charge_id,
        provider_payment_charge_id=provider_charge_id,
        recipient_username=order.recipient_username,
    )

    settings = get_settings()
    recipient = f"@{order.recipient_username}" if order and order.recipient_username else "не указан"

    await message.answer(
        f"✅ <b>Оплата получена!</b>\n\n"
        f"📦 Заказ <b>#{order_id}</b>\n"
        f"⭐ <b>{order.stars} Stars</b> для {recipient}\n\n"
        f"⏱ {settings.SLA_TEXT}\n\n"
        f"<i>Исполнение производится оператором вручную. "
        f"Следить за статусом: «📋 Мои заказы».</i>",
        parse_mode="HTML",
        reply_markup=MAIN_MENU,
    )
    log.info(
        "payment_success",
        order_id=order_id,
        user_id=message.from_user.id if message.from_user else None,
        stars=order.stars if order else None,
        charge_id=telegram_charge_id,
    )

    # Notify admins
    admin_ids = settings.get_admin_ids()
    if admin_ids and message.bot:
        for admin_id in admin_ids:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🔔 <b>Новый оплаченный заказ #{order_id}</b>\n"
                    f"⭐ {order.stars} Stars\n"
                    f"Получатель: {recipient}\n"
                    f"Пользователь: {message.from_user.id if message.from_user else 'N/A'}\n"
                    f"Используйте /admin для просмотра очереди.",
                    parse_mode="HTML",
                )
            except Exception as e:
                log.warning("admin_notify_failed", admin_id=admin_id, error=str(e))
