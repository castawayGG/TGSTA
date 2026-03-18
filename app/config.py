"""Application configuration loaded from environment / .env file."""

from __future__ import annotations

from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Package:
    """Represents a purchasable Stars package."""

    def __init__(self, stars: int, price: int, label: str) -> None:
        self.stars = stars  # number of Stars
        self.price = price  # smallest currency unit (kopecks for RUB)
        self.label = label  # display label, e.g. "100 ⭐"

    def price_rub(self) -> str:
        """Return price formatted as rubles."""
        rubles = self.price / 100
        if rubles == int(rubles):
            return f"{int(rubles)} ₽"
        return f"{rubles:.2f} ₽"

    def __repr__(self) -> str:
        return f"Package(stars={self.stars}, price={self.price}, label={self.label!r})"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Bot
    bot_token: str

    # Payments
    provider_token: str
    currency: str = "RUB"

    # Admin
    admin_ids: list[int] = []

    # Database
    database_url: str = ""  # empty → use SQLite

    # Packages
    packages_json: str = (
        '[{"stars":100,"price":19900,"label":"100 ⭐"},'
        '{"stars":250,"price":44900,"label":"250 ⭐"},'
        '{"stars":500,"price":84900,"label":"500 ⭐"},'
        '{"stars":1000,"price":159900,"label":"1000 ⭐"}]'
    )

    # UX
    order_sla_text: str = "Исполнение вручную — обычно в течение 15–60 минут."
    support_contact: str = "@support"
    terms_url: str = ""
    terms_text: str = ""

    # ── validators ────────────────────────────────────────────────────────────

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Any) -> list[int]:
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return []

    @model_validator(mode="after")
    def set_default_database_url(self) -> Settings:
        if not self.database_url:
            self.database_url = "sqlite+aiosqlite:///./data/app.db"
        return self

    # ── helpers ───────────────────────────────────────────────────────────────

    def get_packages(self) -> list[Package]:
        """Parse and return configured packages (validated)."""
        from app.utils.validators import parse_packages_json  # avoid circular import

        raw = parse_packages_json(self.packages_json)
        return [Package(stars=p["stars"], price=p["price"], label=p["label"]) for p in raw]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    @property
    def effective_terms(self) -> str:
        """Return terms text or URL."""
        if self.terms_text.strip():
            return self.terms_text.strip()
        if self.terms_url.strip():
            return self.terms_url.strip()
        return "Правила не настроены. Обратитесь к администратору."


settings = Settings()  # type: ignore[call-arg]
