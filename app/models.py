"""SQLAlchemy ORM models."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(enum.StrEnum):
    created = "created"
    awaiting_username = "awaiting_username"
    awaiting_payment = "awaiting_payment"
    paid = "paid"
    processing = "processing"
    needs_info = "needs_info"
    done = "done"
    canceled = "canceled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    orders: Mapped[list[Order]] = relationship("Order", back_populates="user", lazy="dynamic")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    stars: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)  # kopecks
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    package_label: Mapped[str] = mapped_column(String(64), default="")

    # Recipient
    recipient_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Status
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.created, index=True
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Payment details
    telegram_payment_charge_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="orders")

    @property
    def price_rub(self) -> str:
        rubles = self.price / 100
        if rubles == int(rubles):
            return f"{int(rubles)} ₽"
        return f"{rubles:.2f} ₽"

    @property
    def status_emoji(self) -> str:
        mapping = {
            OrderStatus.created: "🆕",
            OrderStatus.awaiting_username: "✏️",
            OrderStatus.awaiting_payment: "💳",
            OrderStatus.paid: "💰",
            OrderStatus.processing: "📌",
            OrderStatus.needs_info: "❓",
            OrderStatus.done: "✅",
            OrderStatus.canceled: "❌",
        }
        return mapping.get(self.status, "❔")
