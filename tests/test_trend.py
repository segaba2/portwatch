"""Tests for portwatch.trend and portwatch.trend_hooks."""

import pytest

from portwatch.alerts import PortChange
from portwatch.trend import TrendPoint, TrendSummary, compute_trends, record_changes
import portwatch.trend_hooks as hooks


def _change(host: str, port: int, change_type: str, protocol: str = "tcp") -> PortChange:
    return PortChange(host=host, port=port, change_type=change_type, protocol=protocol, service="")


@pytest.fixture(autouse=True)
def _reset():
    hooks.reset()
    yield
    hooks.reset()


class TestTrendPoint:
    def test_round_trip(self):
        tp = TrendPoint(timestamp="2024-01-01T00:00:00+00:00", change_type="opened",
                        port=80, host="10.0.0.1", protocol="tcp")
        assert TrendPoint.from_dict(tp.as_dict()) == tp

    def test_as_dict_keys(self):
        tp = TrendPoint(timestamp="t", change_type="closed", port=443, host="h", protocol="udp")
        d = tp.as_dict()
        assert set(d.keys()) == {"timestamp", "change_type", "port", "host", "protocol"}

    def test_from_dict_default_protocol(self):
        d = {"timestamp": "t", "change_type": "opened", "port": 22, "host": "h"}
        tp = TrendPoint.from_dict(d)
        assert tp.protocol == "tcp"


class TestRecordChanges:
    def test_appends_points(self):
        pts = record_changes([], [_change("h", 80, "opened"), _change("h", 80, "closed")])
        assert len(pts) == 2

    def test_preserves_existing_points(self):
        existing = [TrendPoint("t", "opened", 22, "h", "tcp")]
        pts = record_changes(existing, [_change("h", 80, "opened")])
        assert len(pts) == 2

    def test_change_type_stored_correctly(self):
        pts = record_changes([], [_change("h", 8080, "closed")])
        assert pts[0].change_type == "closed"
        assert pts[0].port == 8080


class TestComputeTrends:
    def test_single_open(self):
        pts = record_changes([], [_change("h", 80, "opened")])
        trends = compute_trends(pts)
        assert "h:80/tcp" in trends
        assert trends["h:80/tcp"].open_count == 1
        assert trends["h:80/tcp"].close_count == 0

    def test_flap_detection(self):
        changes = [
            _change("h", 80, "opened"),
            _change("h", 80, "closed"),
            _change("h", 80, "opened"),
            _change("h", 80, "closed"),
        ]
        pts = record_changes([], changes)
        trends = compute_trends(pts)
        s = trends["h:80/tcp"]
        assert s.is_flapping
        assert s.flap_count >= 2

    def test_no_flap_when_consistent(self):
        changes = [_change("h", 443, "opened"), _change("h", 443, "opened")]
        pts = record_changes([], changes)
        trends = compute_trends(pts)
        assert not trends["h:443/tcp"].is_flapping

    def test_multiple_hosts_tracked_separately(self):
        changes = [_change("h1", 22, "opened"), _change("h2", 22, "opened")]
        pts = record_changes([], changes)
        trends = compute_trends(pts)
        assert "h1:22/tcp" in trends
        assert "h2:22/tcp" in trends


class TestTrendHooks:
    def test_ingest_increases_point_count(self):
        hooks.ingest_changes([_change("h", 80, "opened")])
        assert hooks.get_point_count() == 1

    def test_get_trends_returns_summaries(self):
        hooks.ingest_changes([_change("h", 80, "opened")])
        trends = hooks.get_trends()
        assert "h:80/tcp" in trends

    def test_get_flapping_empty_when_no_flap(self):
        hooks.ingest_changes([_change("h", 80, "opened")])
        assert hooks.get_flapping() == []

    def test_get_flapping_returns_flapping_entries(self):
        for ct in ["opened", "closed", "opened", "closed"]:
            hooks.ingest_changes([_change("h", 80, ct)])
        assert len(hooks.get_flapping()) == 1

    def test_flapping_summary_no_flap(self):
        assert "No flapping" in hooks.flapping_summary()

    def test_flapping_summary_with_flap(self):
        for ct in ["opened", "closed", "opened", "closed"]:
            hooks.ingest_changes([_change("h", 80, ct)])
        summary = hooks.flapping_summary()
        assert "h:80/tcp" in summary

    def test_reset_clears_points(self):
        hooks.ingest_changes([_change("h", 80, "opened")])
        hooks.reset()
        assert hooks.get_point_count() == 0
