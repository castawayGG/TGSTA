"""My orders handler."""
from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.db.crud import get_user_orders
from bot.db.models import OrderStatus
from bot.keyboards.main import MAIN_MENU

log = structlog.get_logger()
router = Router()

STATUS_EMOJI: dict[OrderStatus, str] = {
    OrderStatus.created: "🆕",
    OrderStatus.awaiting_username: "⌛",
    OrderStatus.invoice_sent: "📨",
    OrderStatus.paid: "💰",
    OrderStatus.processing: "🔄",
    OrderStatus.completed: "✅",
    OrderStatus.cancelled: "❌",
    OrderStatus.clarification_requested: "💬",
}

STATUS_TEXT: dict[OrderStatus, str] = {
    OrderStatus.created: "Создан",
    OrderStatus.awaiting_username: "Ожидание получателя",
    OrderStatus.invoice_sent: "Счёт выставлен",
    OrderStatus.paid: "Оплачен",
    OrderStatus.processing: "В обработке",
    OrderStatus.completed: "Исполнен",
    OrderStatus.cancelled: "Отменён",
    OrderStatus.clarification_requested: "Требует уточнения",
}


@router.message(F.text == "📋 Мои заказы")
async def my_orders_handler(message: Message, session: AsyncSession) -> None:
    settings = get_settings()
    user = message.from_user
    if not user:
        return

    orders = await get_user_orders(session, user.id, limit=settings.ORDERS_LIMIT)

    if not orders:
        await message.answer(
            "У вас пока нет заказов.\nНажмите <b>⭐ Купить Stars</b>, чтобы создать первый!",
            parse_mode="HTML",
            reply_markup=MAIN_MENU,
        )
        return

    lines = ["📋 <b>Ваши последние заказы:</b>\n"]
    for order in orders:
        emoji = STATUS_EMOJI.get(order.status, "❓")
        status_label = STATUS_TEXT.get(order.status, order.status)
        recipient = f"@{order.recipient_username}" if order.recipient_username else "не указан"
        lines.append(
            f"#{order.id} | ⭐ {order.stars} | {order.price_rub // 100} ₽ | "
            f"Получатель: {recipient}\n"
            f"   {emoji} {status_label}"
        )
        if order.admin_note and order.status == OrderStatus.clarification_requested:
            lines.append(f"   💬 {order.admin_note}")

    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=MAIN_MENU)
    log.info("user_orders_viewed", user_id=user.id, count=len(orders))
