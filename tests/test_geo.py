"""Tests for portwatch.geo GeoIP enrichment module."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from portwatch.geo import (
    GeoInfo,
    lookup,
    reset_cache,
    enrich,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


class TestGeoInfo:
    def test_as_dict_structure(self):
        g = GeoInfo(ip="1.2.3.4", country_code="US", country_name="United States", city="New York", asn="AS1234", org="Example")
        d = g.as_dict()
        assert d["ip"] == "1.2.3.4"
        assert d["country_code"] == "US"
        assert d["country_name"] == "United States"
        assert d["city"] == "New York"
        assert d["asn"] == "AS1234"
        assert d["org"] == "Example"

    def test_from_dict_round_trip(self):
        original = GeoInfo(ip="5.6.7.8", country_code="DE", country_name="Germany", city="Berlin", asn="AS99", org="ISP")
        restored = GeoInfo.from_dict(original.as_dict())
        assert restored.ip == original.ip
        assert restored.country_code == original.country_code
        assert restored.city == original.city

    def test_from_dict_missing_fields_default_empty(self):
        g = GeoInfo.from_dict({"ip": "9.9.9.9"})
        assert g.country_code == ""
        assert g.city == ""
        assert g.asn == ""

    def test_str_with_city_and_country(self):
        g = GeoInfo(ip="1.1.1.1", country_name="Australia", city="Sydney")
        assert "Sydney" in str(g)
        assert "Australia" in str(g)

    def test_str_unknown_when_no_location(self):
        g = GeoInfo(ip="1.1.1.1")
        assert "Unknown" in str(g)

    def test_str_country_only(self):
        g = GeoInfo(ip="1.1.1.1", country_name="France")
        result = str(g)
        assert "France" in result


class TestLookup:
    def test_returns_geo_info_instance(self):
        result = lookup("127.0.0.1")
        assert isinstance(result, GeoInfo)
        assert result.ip == "127.0.0.1"

    def test_cache_is_used_on_second_call(self):
        first = lookup("10.0.0.1")
        second = lookup("10.0.0.1")
        assert first is second

    def test_fallback_when_no_geoip2(self):
        with patch.dict("sys.modules", {"geoip2": None, "geoip2.database": None}):
            reset_cache()
            result = lookup("192.168.1.1")
        assert result.ip == "192.168.1.1"
        assert result.country_code == ""


class TestEnrich:
    def test_returns_none_on_unresolvable_host(self):
        with patch("socket.gethostbyname", side_effect=OSError):
            result = enrich("not.a.real.host.invalid")
        assert result is None

    def test_returns_geo_info_on_resolvable_host(self):
        with patch("socket.gethostbyname", return_value="1.2.3.4"):
            result = enrich("example.com")
        assert isinstance(result, GeoInfo)
        assert result.ip == "1.2.3.4"

    def test_caches_result_by_ip(self):
        with patch("socket.gethostbyname", return_value="8.8.8.8"):
            r1 = enrich("dns1.example.com")
            r2 = enrich("dns2.example.com")
        assert r1 is r2
