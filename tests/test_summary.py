"""Tests for portwatch.summary."""

import pytest

from portwatch.scanner import PortState
from portwatch.alerts import PortChange
from portwatch.reporter import ScanReport
from portwatch.summary import build_summary, build_short_summary, SummaryLine


def _state(host: str, port: int, open_: bool = True, proto: str = "tcp") -> PortState:
    return PortState(host=host, port=port, is_open=open_, protocol=proto, service="unknown")


def _change(kind: str, host: str = "10.0.0.1", port: int = 80) -> PortChange:
    return PortChange(kind=kind, host=host, port=port, protocol="tcp", service="http")


class TestSummaryLine:
    def test_str_includes_icon_and_message(self):
        sl = SummaryLine(icon="[+]", message="host:80/tcp opened")
        result = str(sl)
        assert "[+]" in result
        assert "host:80/tcp opened" in result


class TestBuildSummary:
    def test_no_changes_message(self):
        states = [_state("192.168.1.1", 22)]
        report = ScanReport(states=states, changes=[])
        result = build_summary(report)
        assert "No changes detected" in result

    def test_host_count(self):
        states = [_state("10.0.0.1", 22), _state("10.0.0.2", 80)]
        report = ScanReport(states=states, changes=[])
        result = build_summary(report)
        assert "2 host(s) scanned" in result

    def test_open_port_count(self):
        states = [
            _state("10.0.0.1", 22, open_=True),
            _state("10.0.0.1", 81, open_=False),
        ]
        report = ScanReport(states=states, changes=[])
        result = build_summary(report)
        assert "Open ports : 1" in result

    def test_change_count_shown(self):
        states = [_state("10.0.0.1", 80)]
        changes = [_change("opened")]
        report = ScanReport(states=states, changes=changes)
        result = build_summary(report)
        assert "Changes    : 1" in result

    def test_opened_change_icon(self):
        states = [_state("10.0.0.1", 80)]
        changes = [_change("opened", port=80)]
        report = ScanReport(states=states, changes=changes)
        result = build_summary(report)
        assert "[+]" in result

    def test_closed_change_icon(self):
        states = [_state("10.0.0.1", 22, open_=False)]
        changes = [_change("closed", port=22)]
        report = ScanReport(states=states, changes=changes)
        result = build_summary(report)
        assert "[-]" in result

    def test_changed_change_icon(self):
        states = [_state("10.0.0.1", 443)]
        changes = [_change("changed", port=443)]
        report = ScanReport(states=states, changes=changes)
        result = build_summary(report)
        assert "[~]" in result


class TestBuildShortSummary:
    def test_no_changes(self):
        states = [_state("10.0.0.1", 22)]
        report = ScanReport(states=states, changes=[])
        result = build_short_summary(report)
        assert "no changes" in result
        assert "portwatch:" in result

    def test_with_changes(self):
        states = [_state("10.0.0.1", 80)]
        changes = [_change("opened")]
        report = ScanReport(states=states, changes=changes)
        result = build_short_summary(report)
        assert "1 change(s) detected" in result

    def test_single_line(self):
        states = [_state("10.0.0.1", 22)]
        report = ScanReport(states=states, changes=[])
        result = build_short_summary(report)
        assert "\n" not in result
