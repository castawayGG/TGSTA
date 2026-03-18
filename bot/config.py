from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Package:
    def __init__(self, stars: int, price_rub: int) -> None:
        self.stars = stars
        self.price_rub = price_rub

    def __repr__(self) -> str:  # pragma: no cover
        return f"Package(stars={self.stars}, price_rub={self.price_rub})"


def parse_packages(raw: str) -> list[Package]:
    """Parse PACKAGES_JSON environment variable into a list of Package objects."""
    try:
        data: list[dict[str, Any]] = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"PACKAGES_JSON is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError("PACKAGES_JSON must be a JSON array")
    packages: list[Package] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Each package must be an object, got: {item!r}")
        stars = item.get("stars")
        price = item.get("price_rub")
        if not isinstance(stars, int) or stars <= 0:
            raise ValueError(f"Package 'stars' must be a positive int, got: {stars!r}")
        if not isinstance(price, int) or price <= 0:
            raise ValueError(f"Package 'price_rub' must be a positive int, got: {price!r}")
        packages.append(Package(stars=stars, price_rub=price))
    if not packages:
        raise ValueError("PACKAGES_JSON must contain at least one package")
    return packages


_DEFAULT_PACKAGES = json.dumps(
    [
        {"stars": 100, "price_rub": 199},
        {"stars": 250, "price_rub": 449},
        {"stars": 500, "price_rub": 849},
        {"stars": 1000, "price_rub": 1599},
    ]
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Bot
    BOT_TOKEN: str

    # Payments
    PROVIDER_TOKEN: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # Packages
    PACKAGES_JSON: str = _DEFAULT_PACKAGES

    # Admin
    ADMIN_IDS: str = ""  # comma-separated list of Telegram user IDs

    # SLA text shown to user after payment
    SLA_TEXT: str = "Заказ будет исполнен в течение 5–30 минут (в рабочее время)."

    # Max orders shown in "My Orders"
    ORDERS_LIMIT: int = 10

    @field_validator("PACKAGES_JSON")
    @classmethod
    def validate_packages(cls, v: str) -> str:
        parse_packages(v)  # raises ValueError if invalid
        return v

    @model_validator(mode="after")
    def parse_admin_ids(self) -> "Settings":
        return self

    def get_packages(self) -> list[Package]:
        return parse_packages(self.PACKAGES_JSON)

    def get_admin_ids(self) -> list[int]:
        if not self.ADMIN_IDS.strip():
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
