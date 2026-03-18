"""Tests for username validation."""

from bot.utils.validators import normalize_username, validate_telegram_username


class TestValidateTelegramUsername:
    def test_valid_username(self):
        assert validate_telegram_username("validuser") is True

    def test_valid_with_underscores(self):
        assert validate_telegram_username("valid_user_name") is True

    def test_valid_5_chars(self):
        assert validate_telegram_username("abcde") is True

    def test_valid_32_chars(self):
        assert validate_telegram_username("a" * 32) is True

    def test_too_short(self):
        assert validate_telegram_username("abcd") is False

    def test_too_long(self):
        assert validate_telegram_username("a" * 33) is False

    def test_starts_with_underscore(self):
        assert validate_telegram_username("_invalid") is False

    def test_ends_with_underscore(self):
        assert validate_telegram_username("invalid_") is False

    def test_consecutive_underscores(self):
        assert validate_telegram_username("inva__lid") is False

    def test_invalid_chars(self):
        assert validate_telegram_username("user@name") is False
        assert validate_telegram_username("user name") is False
        assert validate_telegram_username("user-name") is False

    def test_empty_string(self):
        assert validate_telegram_username("") is False

    def test_with_at_prefix(self):
        # validate_telegram_username expects no @
        assert validate_telegram_username("@username") is False

    def test_numbers_only(self):
        assert validate_telegram_username("12345") is True

    def test_mixed(self):
        assert validate_telegram_username("user123") is True


class TestNormalizeUsername:
    def test_plain_username(self):
        assert normalize_username("validuser") == "validuser"

    def test_with_at_prefix(self):
        assert normalize_username("@validuser") == "validuser"

    def test_tme_link(self):
        assert normalize_username("t.me/validuser") == "validuser"

    def test_https_tme_link(self):
        assert normalize_username("https://t.me/validuser") == "validuser"

    def test_tme_with_query(self):
        assert normalize_username("t.me/validuser?start=abc") == "validuser"

    def test_invalid_returns_none(self):
        assert normalize_username("ab") is None
        assert normalize_username("user name") is None
        assert normalize_username("") is None

    def test_strips_whitespace(self):
        assert normalize_username("  @validuser  ") == "validuser"

    def test_short_username_invalid(self):
        assert normalize_username("@ab") is None
