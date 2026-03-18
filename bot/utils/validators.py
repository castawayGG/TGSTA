"""Username validation utilities."""
from __future__ import annotations

import re


def validate_telegram_username(username: str) -> bool:
    """
    Validate a Telegram @username (without the @ prefix).

    Rules:
    - Length: 5 to 32 characters
    - Allowed chars: a-z, A-Z, 0-9, underscore
    - Cannot start or end with underscore
    - Cannot have consecutive underscores
    """
    if not username:
        return False
    if len(username) < 5 or len(username) > 32:
        return False
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False
    if username.startswith("_") or username.endswith("_"):
        return False
    if "__" in username:
        return False
    return True


def normalize_username(raw: str) -> str | None:
    """
    Normalize and validate a username input.
    Accepts formats: @username, username, t.me/username
    Returns normalized username (without @) or None if invalid.
    """
    raw = raw.strip()
    # Handle t.me/ links
    if "t.me/" in raw:
        parts = raw.split("t.me/")
        raw = parts[-1].split("/")[0].split("?")[0]
    # Strip leading @
    if raw.startswith("@"):
        raw = raw[1:]
    if validate_telegram_username(raw):
        return raw
    return None
