"""CRUD operations."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Order, OrderStatus, User


async def get_or_create_user(
    session: AsyncSession, user_id: int, username: str | None, full_name: str
) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=user_id, username=username, full_name=full_name)
        session.add(user)
        await session.flush()
    else:
        user.username = username
        user.full_name = full_name
        await session.flush()
    return user


async def create_order(
    session: AsyncSession,
    user_id: int,
    stars: int,
    price_rub: int,
    status: OrderStatus = OrderStatus.created,
) -> Order:
    order = Order(
        user_id=user_id,
        stars=stars,
        price_rub=price_rub,
        status=status,
    )
    session.add(order)
    await session.flush()
    return order


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_order_by_charge_id(
    session: AsyncSession, telegram_payment_charge_id: str
) -> Order | None:
    result = await session.execute(
        select(Order).where(Order.telegram_payment_charge_id == telegram_payment_charge_id)
    )
    return result.scalar_one_or_none()


async def get_user_orders(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_pending_orders(session: AsyncSession) -> list[Order]:
    """Orders waiting for admin action."""
    result = await session.execute(
        select(Order)
        .where(Order.status.in_([OrderStatus.paid, OrderStatus.processing]))
        .order_by(Order.created_at.asc())
    )
    return list(result.scalars().all())


async def update_order_status(
    session: AsyncSession,
    order_id: int,
    status: OrderStatus,
    admin_note: str | None = None,
) -> Order | None:
    order = await get_order(session, order_id)
    if order is None:
        return None
    order.status = status
    if admin_note is not None:
        order.admin_note = admin_note
    await session.flush()
    return order


async def mark_order_paid(
    session: AsyncSession,
    order_id: int,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: str,
    recipient_username: str | None,
) -> Order | None:
    order = await get_order(session, order_id)
    if order is None:
        return None
    order.status = OrderStatus.paid
    order.telegram_payment_charge_id = telegram_payment_charge_id
    order.provider_payment_charge_id = provider_payment_charge_id
    if recipient_username:
        order.recipient_username = recipient_username
    await session.flush()
    return order
