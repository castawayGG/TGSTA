"""Tests for PACKAGES_JSON parsing."""

import pytest

from app.utils.validators import parse_packages_json

VALID_JSON = (
    '[{"stars":100,"price":19900,"label":"100 ⭐"},'
    '{"stars":250,"price":44900,"label":"250 ⭐"}]'
)


def test_parse_valid_packages() -> None:
    pkgs = parse_packages_json(VALID_JSON)
    assert len(pkgs) == 2
    assert pkgs[0]["stars"] == 100
    assert pkgs[0]["price"] == 19900
    assert pkgs[0]["label"] == "100 ⭐"
    assert pkgs[1]["stars"] == 250


def test_parse_default_label() -> None:
    raw = '[{"stars":500,"price":84900}]'
    pkgs = parse_packages_json(raw)
    assert pkgs[0]["label"] == "500 ⭐"


def test_parse_invalid_json() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_packages_json("not json")


def test_parse_not_array() -> None:
    with pytest.raises(ValueError, match="non-empty JSON array"):
        parse_packages_json('{"stars":100,"price":100}')


def test_parse_empty_array() -> None:
    with pytest.raises(ValueError, match="non-empty JSON array"):
        parse_packages_json("[]")


def test_parse_missing_stars() -> None:
    with pytest.raises(ValueError, match="'stars'"):
        parse_packages_json('[{"price":100}]')


def test_parse_missing_price() -> None:
    with pytest.raises(ValueError, match="'price'"):
        parse_packages_json('[{"stars":100}]')


def test_parse_negative_stars() -> None:
    with pytest.raises(ValueError, match="'stars'"):
        parse_packages_json('[{"stars":-1,"price":100}]')


def test_parse_zero_price() -> None:
    with pytest.raises(ValueError, match="'price'"):
        parse_packages_json('[{"stars":100,"price":0}]')


def test_parse_string_stars() -> None:
    with pytest.raises(ValueError, match="'stars'"):
        parse_packages_json('[{"stars":"100","price":100}]')
