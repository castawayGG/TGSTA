"""Tests for username validation."""

import pytest

from app.utils.validators import normalize_username, validate_username


@pytest.mark.parametrize(
    "username,expected",
    [
        # Valid usernames
        ("@durov", True),
        ("durov", True),
        ("@user_name", True),
        ("username123", True),
        ("@a1b2c3d4e", True),
        ("@john_doe_1", True),
        ("@abcde", True),  # exactly 5 chars
        # Invalid: too short
        ("@ab", False),
        ("ab", False),
        ("@abc", False),  # 3 chars, need ≥5
        # Invalid: starts with digit
        ("@1username", False),
        # Invalid: consecutive underscores
        ("@user__name", False),
        # Invalid: ends with underscore
        ("@username_", False),
        # Invalid: contains unsupported chars
        ("@user-name", False),
        ("@user name", False),
        ("@user.name", False),
        # Invalid: empty
        ("", False),
        ("@", False),
    ],
)
def test_validate_username(username: str, expected: bool) -> None:
    assert validate_username(username) == expected, f"Failed for {username!r}"


def test_normalize_username_strips_at() -> None:
    assert normalize_username("@Durov") == "durov"


def test_normalize_username_no_at() -> None:
    assert normalize_username("Durov") == "durov"


def test_normalize_username_lowercase() -> None:
    assert normalize_username("@TestUser123") == "testuser123"
