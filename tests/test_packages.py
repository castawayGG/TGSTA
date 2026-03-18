"""Tests for PACKAGES_JSON parsing."""
import json

import pytest

from bot.config import Package, parse_packages


class TestParsePackages:
    def test_valid_single_package(self):
        raw = json.dumps([{"stars": 100, "price_rub": 199}])
        packages = parse_packages(raw)
        assert len(packages) == 1
        assert packages[0].stars == 100
        assert packages[0].price_rub == 199

    def test_valid_multiple_packages(self):
        raw = json.dumps([
            {"stars": 100, "price_rub": 199},
            {"stars": 250, "price_rub": 449},
            {"stars": 500, "price_rub": 849},
            {"stars": 1000, "price_rub": 1599},
        ])
        packages = parse_packages(raw)
        assert len(packages) == 4
        assert packages[0].stars == 100
        assert packages[3].stars == 1000
        assert packages[3].price_rub == 1599

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="PACKAGES_JSON is not valid JSON"):
            parse_packages("{not: json}")

    def test_not_a_list(self):
        with pytest.raises(ValueError, match="must be a JSON array"):
            parse_packages(json.dumps({"stars": 100, "price_rub": 199}))

    def test_empty_list(self):
        with pytest.raises(ValueError, match="at least one package"):
            parse_packages(json.dumps([]))

    def test_missing_stars(self):
        with pytest.raises(ValueError, match="'stars'"):
            parse_packages(json.dumps([{"price_rub": 199}]))

    def test_missing_price(self):
        with pytest.raises(ValueError, match="'price_rub'"):
            parse_packages(json.dumps([{"stars": 100}]))

    def test_negative_stars(self):
        with pytest.raises(ValueError, match="'stars'"):
            parse_packages(json.dumps([{"stars": -1, "price_rub": 199}]))

    def test_zero_price(self):
        with pytest.raises(ValueError, match="'price_rub'"):
            parse_packages(json.dumps([{"stars": 100, "price_rub": 0}]))

    def test_string_stars(self):
        with pytest.raises(ValueError, match="'stars'"):
            parse_packages(json.dumps([{"stars": "100", "price_rub": 199}]))

    def test_package_repr(self):
        pkg = Package(stars=100, price_rub=199)
        assert "100" in repr(pkg)
        assert "199" in repr(pkg)

    def test_item_not_dict(self):
        with pytest.raises(ValueError, match="object"):
            parse_packages(json.dumps([42]))
