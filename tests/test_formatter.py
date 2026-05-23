"""Tests for portwatch.formatter."""

import json
import pytest

from portwatch.scanner import PortState
from portwatch.alerts import PortChange
from portwatch.reporter import ScanReport
from portwatch.formatter import (
    format_report,
    available_formats,
    register_formatter,
)


def _state(host: str, port: int, open_: bool = True, service: str = "http") -> PortState:
    return PortState(host=host, port=port, is_open=open_, protocol="tcp", service=service)


def _simple_report() -> ScanReport:
    states = [
        _state("10.0.0.1", 80, open_=True, service="http"),
        _state("10.0.0.1", 22, open_=False, service="ssh"),
    ]
    changes = [PortChange(kind="opened", host="10.0.0.1", port=80, protocol="tcp", service="http")]
    return ScanReport(states=states, changes=changes)


class TestAvailableFormats:
    def test_contains_text(self):
        assert "text" in available_formats()

    def test_contains_json(self):
        assert "json" in available_formats()

    def test_contains_csv(self):
        assert "csv" in available_formats()


class TestFormatText:
    def test_returns_string(self):
        result = format_report(_simple_report(), fmt="text")
        assert isinstance(result, str)

    def test_contains_host(self):
        result = format_report(_simple_report(), fmt="text")
        assert "10.0.0.1" in result

    def test_contains_change_marker(self):
        result = format_report(_simple_report(), fmt="text")
        assert "[+]" in result


class TestFormatJson:
    def test_valid_json(self):
        result = format_report(_simple_report(), fmt="json")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_has_states_key(self):
        result = format_report(_simple_report(), fmt="json")
        parsed = json.loads(result)
        assert "states" in parsed

    def test_has_changes_key(self):
        result = format_report(_simple_report(), fmt="json")
        parsed = json.loads(result)
        assert "changes" in parsed


class TestFormatCsv:
    def test_has_header(self):
        result = format_report(_simple_report(), fmt="csv")
        assert result.startswith("host,port,protocol,service,is_open")

    def test_rows_contain_host(self):
        result = format_report(_simple_report(), fmt="csv")
        assert "10.0.0.1" in result

    def test_row_count(self):
        result = format_report(_simple_report(), fmt="csv")
        rows = result.strip().splitlines()
        # 1 header + 2 state rows
        assert len(rows) == 3


class TestUnknownFormat:
    def test_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown format"):
            format_report(_simple_report(), fmt="xml")


class TestRegisterFormatter:
    def test_custom_formatter_is_used(self):
        register_formatter("upper", lambda r: "CUSTOM")
        result = format_report(_simple_report(), fmt="upper")
        assert result == "CUSTOM"

    def test_custom_format_appears_in_available(self):
        register_formatter("myformat", lambda r: "")
        assert "myformat" in available_formats()
