"""Telegram Payments handlers: pre_checkout_query + successful_payment."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

from app.config import settings
from app.database import async_session_factory
from app.models import Order, OrderStatus

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    """Validate order before Telegram finalises the payment."""
    payload = query.invoice_payload  # e.g. "order:42"
    if not payload.startswith("order:"):
        await query.answer(ok=False, error_message="Неверный payload заказа.")
        return

    order_id = int(payload.split(":")[1])
    async with async_session_factory() as session:
        order = await session.get(Order, order_id)

    if order is None:
        await query.answer(ok=False, error_message="Заказ не найден.")
        return

    if order.status not in (OrderStatus.awaiting_payment,):
        # Idempotency: already paid → still allow (Telegram may resend)
        if order.status == OrderStatus.paid:
            await query.answer(ok=True)
            return
        await query.answer(ok=False, error_message="Заказ уже завершён или отменён.")
        return

    await query.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: Message) -> None:
    """Handle confirmed payment — idempotently mark order as paid."""
    sp = message.successful_payment
    if sp is None:
        return

    payload = sp.invoice_payload
    if not payload.startswith("order:"):
        return

    order_id = int(payload.split(":")[1])

    async with async_session_factory() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await message.answer("⚠️ Заказ не найден — обратитесь в поддержку.")
            return

        if order.status != OrderStatus.paid:
            # Idempotent: only update if not yet paid
            order.status = OrderStatus.paid
            order.telegram_payment_charge_id = sp.telegram_payment_charge_id
            order.provider_payment_charge_id = sp.provider_payment_charge_id
            order.paid_at = datetime.now(UTC)
            await session.commit()

    await message.answer(
        "✅ <b>Оплата получена!</b>\n\n"
        f"📦 Пакет: <b>{order.package_label}</b>\n"
        f"👤 Получатель: <code>@{order.recipient_username}</code>\n"
        f"💰 Сумма: <b>{order.price_rub}</b>\n"
        f"🔖 Заказ: <code>#{order.id}</code>\n\n"
        f"⏳ {settings.order_sla_text}\n"
        "Как только заказ будет исполнен — вы получите уведомление.",
        parse_mode="HTML",
    )

    # Notify all admins about a new paid order
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(  # type: ignore[union-attr]
                chat_id=admin_id,
                text=(
                    "🔔 <b>Новый оплаченный заказ!</b>\n\n"
                    f"🔖 Заказ: <code>#{order.id}</code>\n"
                    f"👤 Получатель: <code>@{order.recipient_username}</code>\n"
                    f"📦 Пакет: <b>{order.package_label}</b>\n"
                    f"💰 Сумма: <b>{order.price_rub}</b>\n"
                    f"🆔 Покупатель: <code>{message.from_user.id}</code>\n\n"  # type: ignore[union-attr]
                    "Используйте /admin для управления заказами."
                ),
                parse_mode="HTML",
            )
        except Exception:  # noqa: BLE001
                logger.warning("Could not notify admin %s", admin_id, exc_info=True)
