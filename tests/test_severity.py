"""Tests for portwatch.severity."""

from __future__ import annotations

import pytest

from portwatch.alerts import PortChange
from portwatch.severity import (
    SeverityLevel,
    SeverityResult,
    classify,
    classify_all,
    highest_severity,
)


def _change(port: int, kind: str = "opened", host: str = "192.168.1.1") -> PortChange:
    return PortChange(host=host, port=port, protocol="tcp", kind=kind)


# ---------------------------------------------------------------------------
# classify()
# ---------------------------------------------------------------------------

class TestClassify:
    def test_critical_port_opened(self):
        result = classify(_change(22, "opened"))
        assert result.level == SeverityLevel.CRITICAL

    def test_rdp_port_critical(self):
        result = classify(_change(3389, "opened"))
        assert result.level == SeverityLevel.CRITICAL

    def test_high_port_opened(self):
        result = classify(_change(3306, "opened"))
        assert result.level == SeverityLevel.HIGH

    def test_privileged_port_opened(self):
        # Port 80 is not in critical/high lists but is < 1024
        result = classify(_change(80, "opened"))
        assert result.level == SeverityLevel.MEDIUM

    def test_unprivileged_port_opened(self):
        result = classify(_change(8080, "opened"))
        assert result.level == SeverityLevel.LOW

    def test_critical_port_closed_is_medium(self):
        result = classify(_change(22, "closed"))
        assert result.level == SeverityLevel.MEDIUM

    def test_high_port_closed_is_medium(self):
        result = classify(_change(3306, "closed"))
        assert result.level == SeverityLevel.MEDIUM

    def test_ordinary_port_closed_is_info(self):
        result = classify(_change(9000, "closed"))
        assert result.level == SeverityLevel.INFO

    def test_reason_is_non_empty(self):
        result = classify(_change(22, "opened"))
        assert result.reason

    def test_as_dict_keys(self):
        result = classify(_change(22, "opened"))
        d = result.as_dict()
        assert "host" in d
        assert "port" in d
        assert "severity" in d
        assert "reason" in d
        assert d["severity"] == "critical"


# ---------------------------------------------------------------------------
# classify_all()
# ---------------------------------------------------------------------------

class TestClassifyAll:
    def test_empty_list(self):
        assert classify_all([]) == []

    def test_sorted_by_severity(self):
        changes = [
            _change(9000, "opened"),   # LOW
            _change(22, "opened"),     # CRITICAL
            _change(3306, "opened"),   # HIGH
        ]
        results = classify_all(changes)
        levels = [r.level for r in results]
        assert levels == [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.LOW,
        ]

    def test_returns_severity_result_instances(self):
        results = classify_all([_change(80, "opened")])
        assert all(isinstance(r, SeverityResult) for r in results)


# ---------------------------------------------------------------------------
# highest_severity()
# ---------------------------------------------------------------------------

class TestHighestSeverity:
    def test_none_when_empty(self):
        assert highest_severity([]) is None

    def test_single_result(self):
        results = classify_all([_change(22, "opened")])
        assert highest_severity(results) == SeverityLevel.CRITICAL

    def test_mixed_returns_highest(self):
        results = classify_all([
            _change(9000, "opened"),
            _change(3306, "opened"),
        ])
        assert highest_severity(results) == SeverityLevel.HIGH

    def test_all_info(self):
        results = classify_all([_change(9000, "closed")])
        assert highest_severity(results) == SeverityLevel.INFO
