"""Tests for portwatch.anomaly and portwatch.anomaly_hooks."""

from __future__ import annotations

import pytest

from portwatch.anomaly import AnomalyRule, AnomalyResult, detect_anomalies
from portwatch.anomaly_hooks import (
    load_rules,
    get_rules,
    reset_rules,
    run_anomaly_detection,
    flagged_summary,
)
from portwatch.alerts import PortChange


def _change(host="10.0.0.1", port=22, protocol="tcp", kind="opened") -> PortChange:
    return PortChange(host=host, port=port, protocol=protocol, kind=kind)


# ---------------------------------------------------------------------------
# AnomalyRule
# ---------------------------------------------------------------------------

class TestAnomalyRule:
    def test_exact_match(self):
        rule = AnomalyRule(host="10.0.0.1", port=22, protocol="tcp", reason="ssh")
        assert rule.matches(_change())

    def test_wildcard_host(self):
        rule = AnomalyRule(host="*", port=22, protocol="tcp")
        assert rule.matches(_change(host="192.168.1.5"))

    def test_wildcard_protocol(self):
        rule = AnomalyRule(host="10.0.0.1", port=22, protocol="*")
        assert rule.matches(_change(protocol="udp"))

    def test_no_match_wrong_port(self):
        rule = AnomalyRule(host="10.0.0.1", port=80, protocol="tcp")
        assert not rule.matches(_change(port=22))

    def test_no_match_wrong_host(self):
        rule = AnomalyRule(host="10.0.0.2", port=22, protocol="tcp")
        assert not rule.matches(_change(host="10.0.0.1"))

    def test_round_trip(self):
        rule = AnomalyRule(host="h", port=443, protocol="tcp", reason="tls")
        restored = AnomalyRule.from_dict(rule.as_dict())
        assert restored.host == rule.host
        assert restored.port == rule.port
        assert restored.reason == rule.reason


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

class TestDetectAnomalies:
    def test_no_rules_all_clean(self):
        result = detect_anomalies([_change(), _change(port=80)], [])
        assert not result.has_anomalies
        assert len(result.clean) == 2

    def test_matching_rule_flags_change(self):
        rule = AnomalyRule(host="10.0.0.1", port=22, protocol="tcp")
        result = detect_anomalies([_change()], [rule])
        assert result.has_anomalies
        assert len(result.flagged) == 1
        assert result.clean == []

    def test_partial_match(self):
        rule = AnomalyRule(host="10.0.0.1", port=22, protocol="tcp")
        changes = [_change(port=22), _change(port=80)]
        result = detect_anomalies(changes, [rule])
        assert len(result.flagged) == 1
        assert len(result.clean) == 1

    def test_summary_no_anomalies(self):
        result = AnomalyResult()
        assert "No anomalies" in result.summary()

    def test_summary_with_anomalies(self):
        rule = AnomalyRule(host="10.0.0.1", port=22, protocol="tcp", reason="ssh")
        result = detect_anomalies([_change()], [rule])
        text = result.summary()
        assert "10.0.0.1" in text
        assert "ssh" in text


# ---------------------------------------------------------------------------
# anomaly_hooks
# ---------------------------------------------------------------------------

class TestAnomalyHooks:
    def setup_method(self):
        reset_rules()

    def test_load_and_get_rules(self):
        load_rules([{"host": "h1", "port": 22, "protocol": "tcp", "reason": "r"}])
        rules = get_rules()
        assert len(rules) == 1
        assert rules[0].host == "h1"

    def test_reset_clears_rules(self):
        load_rules([{"host": "h1", "port": 22, "protocol": "tcp"}])
        reset_rules()
        assert get_rules() == []

    def test_run_uses_global_rules(self):
        load_rules([{"host": "10.0.0.1", "port": 22, "protocol": "tcp"}])
        result = run_anomaly_detection([_change()])
        assert result.has_anomalies

    def test_flagged_summary_empty_when_clean(self):
        result = run_anomaly_detection([_change()])
        assert flagged_summary(result) == ""

    def test_flagged_summary_contains_host(self):
        load_rules([{"host": "10.0.0.1", "port": 22, "protocol": "tcp", "reason": "ssh"}])
        result = run_anomaly_detection([_change()])
        summary = flagged_summary(result)
        assert "10.0.0.1" in summary
        assert "ssh" in summary
