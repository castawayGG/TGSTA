"""'My orders' handler."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from app.database import async_session_factory
from app.models import Order

router = Router()

PAGE_SIZE = 5


@router.message(F.text == "📋 Мои заказы")
@router.message(Command("orders"))
async def my_orders(message: Message) -> None:
    user_id = message.from_user.id  # type: ignore[union-attr]

    async with async_session_factory() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(PAGE_SIZE)
        )
        orders = result.scalars().all()

    if not orders:
        await message.answer("У вас пока нет заказов. Нажмите «⭐ Купить Stars», чтобы начать.")
        return

    lines = ["📋 <b>Ваши последние заказы:</b>\n"]
    for order in orders:
        created = order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "—"
        updated = order.updated_at.strftime("%d.%m.%Y %H:%M") if order.updated_at else "—"
        lines.append(
            f"{order.status_emoji} <b>Заказ #{order.id}</b>\n"
            f"  📦 {order.package_label}  💰 {order.price_rub}\n"
            f"  👤 @{order.recipient_username or '—'}\n"
            f"  📅 Создан: {created}  |  Обновлён: {updated}\n"
            f"  🏷 Статус: <b>{order.status.value}</b>"
            + (f"\n  💬 {order.admin_comment}" if order.admin_comment else "")
        )

    await message.answer("\n\n".join(lines), parse_mode="HTML")
