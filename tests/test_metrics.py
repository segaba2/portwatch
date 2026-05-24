"""Tests for portwatch.metrics."""
import pytest

from portwatch.metrics import MetricsStore, ScanMetrics, get_metrics, reset_metrics


@pytest.fixture(autouse=True)
def _reset():
    reset_metrics()
    yield
    reset_metrics()


def _m(host="h1", port_count=10, open_count=2, duration=1.0, error=None):
    return ScanMetrics(
        host=host,
        port_count=port_count,
        open_count=open_count,
        duration_seconds=duration,
        error=error,
    )


class TestScanMetrics:
    def test_as_dict_structure(self):
        m = _m()
        d = m.as_dict()
        assert d["host"] == "h1"
        assert d["port_count"] == 10
        assert d["open_count"] == 2
        assert d["duration_seconds"] == 1.0
        assert d["error"] is None

    def test_as_dict_with_error(self):
        m = _m(error="timeout")
        assert m.as_dict()["error"] == "timeout"


class TestMetricsStore:
    def test_empty_defaults(self):
        store = MetricsStore()
        assert store.cycle_count == 0
        assert store.error_count == 0
        assert store.average_scan_duration == 0.0

    def test_record_increments_counts(self):
        store = MetricsStore()
        store.record(_m(duration=2.0))
        store.record(_m(duration=4.0))
        assert store.average_scan_duration == pytest.approx(3.0)

    def test_error_count_increments_on_error(self):
        store = MetricsStore()
        store.record(_m())
        store.record(_m(error="refused"))
        assert store.error_count == 1

    def test_increment_cycle(self):
        store = MetricsStore()
        store.increment_cycle()
        store.increment_cycle()
        assert store.cycle_count == 2

    def test_per_host_summary_groups_correctly(self):
        store = MetricsStore()
        store.record(_m(host="a", duration=1.0))
        store.record(_m(host="a", duration=3.0))
        store.record(_m(host="b", duration=2.0))
        summary = store.per_host_summary()
        assert summary["a"]["scans"] == 2
        assert summary["a"]["avg_duration"] == pytest.approx(2.0)
        assert summary["b"]["scans"] == 1

    def test_as_dict_shape(self):
        store = MetricsStore()
        store.record(_m())
        store.increment_cycle()
        d = store.as_dict()
        assert "cycle_count" in d
        assert "total_scans" in d
        assert "error_count" in d
        assert "average_scan_duration" in d
        assert "per_host" in d


class TestGetAndResetMetrics:
    def test_get_metrics_returns_same_instance(self):
        assert get_metrics() is get_metrics()

    def test_reset_creates_fresh_store(self):
        get_metrics().record(_m())
        reset_metrics()
        assert get_metrics().cycle_count == 0
        assert len(get_metrics()._scans) == 0
