"""Tests for portwatch.suppression."""

from __future__ import annotations

import pytest

from portwatch.alerts import PortChange
from portwatch.suppression import SuppressionList, SuppressionRule


def _change(
    host: str = "192.168.1.1",
    port: int = 80,
    protocol: str = "tcp",
    kind: str = "opened",
) -> PortChange:
    return PortChange(host=host, port=port, protocol=protocol, kind=kind)


class TestSuppressionRule:
    def test_exact_match(self):
        rule = SuppressionRule(host="192.168.1.1", port=80, protocol="tcp")
        assert rule.matches(_change())

    def test_wrong_port_no_match(self):
        rule = SuppressionRule(host="192.168.1.1", port=443, protocol="tcp")
        assert not rule.matches(_change(port=80))

    def test_wrong_host_no_match(self):
        rule = SuppressionRule(host="10.0.0.1", port=80, protocol="tcp")
        assert not rule.matches(_change(host="192.168.1.1"))

    def test_wildcard_host(self):
        rule = SuppressionRule(host="*", port=80, protocol="tcp")
        assert rule.matches(_change(host="10.0.0.5"))

    def test_wildcard_protocol(self):
        rule = SuppressionRule(host="192.168.1.1", port=53, protocol="*")
        assert rule.matches(_change(port=53, protocol="udp"))
        assert rule.matches(_change(port=53, protocol="tcp"))

    def test_round_trip_dict(self):
        rule = SuppressionRule(host="10.0.0.1", port=22, protocol="tcp")
        restored = SuppressionRule.from_dict(rule.as_dict())
        assert restored == rule

    def test_from_dict_default_protocol(self):
        rule = SuppressionRule.from_dict({"host": "h", "port": 8080})
        assert rule.protocol == "tcp"


class TestSuppressionList:
    def test_is_suppressed_true(self):
        sl = SuppressionList(
            rules=[SuppressionRule(host="192.168.1.1", port=80, protocol="tcp")]
        )
        assert sl.is_suppressed(_change())

    def test_is_suppressed_false_when_no_rules(self):
        sl = SuppressionList()
        assert not sl.is_suppressed(_change())

    def test_filter_changes_removes_suppressed(self):
        sl = SuppressionList(
            rules=[SuppressionRule(host="*", port=80, protocol="tcp")]
        )
        changes = [_change(port=80), _change(port=443)]
        result = sl.filter_changes(changes)
        assert len(result) == 1
        assert result[0].port == 443

    def test_filter_changes_empty_list(self):
        sl = SuppressionList(
            rules=[SuppressionRule(host="*", port=22, protocol="tcp")]
        )
        assert sl.filter_changes([]) == []

    def test_from_list_and_as_list_round_trip(self):
        raw = [{"host": "10.0.0.1", "port": 22, "protocol": "tcp"}]
        sl = SuppressionList.from_list(raw)
        assert sl.as_list() == raw

    def test_multiple_rules_any_match_suppresses(self):
        sl = SuppressionList.from_list([
            {"host": "h1", "port": 80, "protocol": "tcp"},
            {"host": "h2", "port": 443, "protocol": "tcp"},
        ])
        assert sl.is_suppressed(_change(host="h2", port=443))
        assert not sl.is_suppressed(_change(host="h3", port=8080))
