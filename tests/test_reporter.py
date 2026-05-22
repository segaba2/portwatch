"""Tests for portwatch.reporter."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from portwatch.reporter import ScanReport, build_report
from portwatch.scanner import PortState
from portwatch.alerts import PortChange


UTC = timezone.utc
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_PREV = datetime(2024, 6, 1, 11, 0, 0, tzinfo=UTC)


def _state(port: int, is_open: bool, service: str = "") -> PortState:
    return PortState(port=port, is_open=is_open, service=service)


def _change(port: int, kind: str, service: str = "") -> PortChange:
    return PortChange(port=port, kind=kind, service=service)


class TestScanReport:
    def _report(self, changes=None):
        ports = [_state(22, True, "ssh"), _state(80, True, "http"), _state(443, False)]
        return ScanReport(
            host="10.0.0.1",
            scanned_at=_NOW,
            ports=ports,
            changes=changes or [],
            previous_scanned_at=_PREV,
        )

    def test_open_ports_filters_correctly(self):
        r = self._report()
        assert len(r.open_ports()) == 2
        assert all(p.is_open for p in r.open_ports())

    def test_has_changes_false_when_empty(self):
        assert not self._report().has_changes()

    def test_has_changes_true_when_present(self):
        r = self._report(changes=[_change(8080, "opened")])
        assert r.has_changes()

    def test_as_dict_structure(self):
        r = self._report(changes=[_change(22, "closed", "ssh")])
        d = r.as_dict()
        assert d["host"] == "10.0.0.1"
        assert d["scanned_at"] == _NOW.isoformat()
        assert d["previous_scanned_at"] == _PREV.isoformat()
        assert len(d["open_ports"]) == 2
        assert len(d["changes"]) == 1
        assert d["changes"][0] == {"port": 22, "service": "ssh", "kind": "closed"}

    def test_as_dict_no_previous(self):
        r = ScanReport(host="h", scanned_at=_NOW, ports=[])
        assert r.as_dict()["previous_scanned_at"] is None

    def test_as_json_is_valid(self):
        r = self._report()
        data = json.loads(r.as_json())
        assert data["host"] == "10.0.0.1"

    def test_as_text_contains_host(self):
        r = self._report()
        text = r.as_text()
        assert "10.0.0.1" in text
        assert "22/tcp" in text
        assert "Changes    : none" in text

    def test_as_text_shows_changes(self):
        r = self._report(changes=[_change(8080, "opened")])
        text = r.as_text()
        assert "[OPENED]" in text
        assert "8080/tcp" in text


class TestBuildReport:
    def test_returns_scan_report(self):
        ports = [_state(22, True, "ssh")]
        r = build_report("192.168.1.1", ports)
        assert r.host == "192.168.1.1"
        assert r.ports == ports
        assert r.scanned_at.tzinfo == UTC

    def test_changes_default_empty(self):
        r = build_report("h", [])
        assert r.changes == []

    def test_previous_scanned_at_passed_through(self):
        r = build_report("h", [], previous_scanned_at=_PREV)
        assert r.previous_scanned_at == _PREV
