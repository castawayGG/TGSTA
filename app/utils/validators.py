"""Utility helpers: username validation, package parsing."""

from __future__ import annotations

import json
import re

_USERNAME_RE = re.compile(r"^@?[a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9]$")


def validate_username(value: str) -> bool:
    """Return True if *value* looks like a valid Telegram @username.

    Rules (approximation of Telegram's rules):
    - 5–32 characters total (excluding the leading @).
    - Starts with a letter, ends with a letter or digit.
    - Contains only letters, digits and underscores.
    - No consecutive underscores.
    """
    if not value:
        return False
    raw = value.lstrip("@")
    if not _USERNAME_RE.match(raw):
        return False
    if "__" in raw:
        return False
    return True


def normalize_username(value: str) -> str:
    """Return username without leading @ and in lowercase."""
    return value.lstrip("@").lower()


def parse_packages_json(raw: str) -> list[dict]:
    """Parse PACKAGES_JSON string into a list of package dicts.

    Each dict must have 'stars' (int > 0) and 'price' (int > 0).
    'label' is optional; defaults to '<stars> ⭐'.

    Raises ValueError on invalid input.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"PACKAGES_JSON is not valid JSON: {exc}") from exc

    if not isinstance(data, list) or not data:
        raise ValueError("PACKAGES_JSON must be a non-empty JSON array")

    result = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"PACKAGES_JSON item #{i} is not an object")
        stars = item.get("stars")
        price = item.get("price")
        if not isinstance(stars, int) or stars <= 0:
            raise ValueError(
                f"PACKAGES_JSON item #{i}: 'stars' must be a positive integer, got {stars!r}"
            )
        if not isinstance(price, int) or price <= 0:
            raise ValueError(
                f"PACKAGES_JSON item #{i}: 'price' must be a positive integer (kopecks), "
                f"got {price!r}"
            )
        label = item.get("label") or f"{stars} ⭐"
        result.append({"stars": stars, "price": price, "label": label})

    return result
