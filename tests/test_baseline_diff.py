"""Tests for portwatch.baseline_diff."""

from datetime import datetime, timezone

import pytest

from portwatch.baseline import Baseline
from portwatch.baseline_diff import (
    BaselineDiffResult,
    any_deviation,
    diff_against_baseline,
)
from portwatch.scanner import PortState


def _bl(states: dict) -> Baseline:
    return Baseline(
        name="test",
        created_at=datetime.now(tz=timezone.utc),
        states=states,
    )


def _s(port: int, open: bool = True, proto: str = "tcp") -> PortState:
    return PortState(port=port, protocol=proto, open=open)


class TestBaselineDiffResult:
    def test_no_deviation_when_empty(self):
        r = BaselineDiffResult(host="h", unexpected_open=[], unexpected_closed=[])
        assert not r.has_deviation

    def test_has_deviation_unexpected_open(self):
        r = BaselineDiffResult(host="h", unexpected_open=[_s(8080)], unexpected_closed=[])
        assert r.has_deviation

    def test_summary_no_deviation(self):
        r = BaselineDiffResult(host="h", unexpected_open=[], unexpected_closed=[])
        assert "no deviation" in r.summary()

    def test_summary_lists_ports(self):
        r = BaselineDiffResult(
            host="h",
            unexpected_open=[_s(8080)],
            unexpected_closed=[_s(22)],
        )
        s = r.summary()
        assert "8080" in s
        assert "22" in s


class TestDiffAgainstBaseline:
    def test_no_deviation_identical(self):
        states = {"host1": [_s(22), _s(80)]}
        results = diff_against_baseline(_bl(states), states)
        assert not any_deviation(results)

    def test_detects_unexpected_open_port(self):
        baseline_states = {"host1": [_s(22)]}
        current_states = {"host1": [_s(22), _s(8080)]}
        results = diff_against_baseline(_bl(baseline_states), current_states)
        host_result = next(r for r in results if r.host == "host1")
        assert len(host_result.unexpected_open) == 1
        assert host_result.unexpected_open[0].port == 8080

    def test_detects_unexpected_closed_port(self):
        baseline_states = {"host1": [_s(22), _s(80)]}
        current_states = {"host1": [_s(22)]}
        results = diff_against_baseline(_bl(baseline_states), current_states)
        host_result = next(r for r in results if r.host == "host1")
        assert len(host_result.unexpected_closed) == 1
        assert host_result.unexpected_closed[0].port == 80

    def test_host_only_in_current(self):
        baseline_states: dict = {}
        current_states = {"newhost": [_s(443)]}
        results = diff_against_baseline(_bl(baseline_states), current_states)
        host_result = next(r for r in results if r.host == "newhost")
        assert host_result.unexpected_open[0].port == 443

    def test_host_only_in_baseline(self):
        baseline_states = {"gone": [_s(22)]}
        current_states: dict = {}
        results = diff_against_baseline(_bl(baseline_states), current_states)
        host_result = next(r for r in results if r.host == "gone")
        assert host_result.unexpected_closed[0].port == 22

    def test_any_deviation_false_when_clean(self):
        states = {"h": [_s(22)]}
        results = diff_against_baseline(_bl(states), states)
        assert not any_deviation(results)

    def test_any_deviation_true_when_dirty(self):
        baseline_states = {"h": [_s(22)]}
        current_states = {"h": [_s(22), _s(9999)]}
        results = diff_against_baseline(_bl(baseline_states), current_states)
        assert any_deviation(results)
