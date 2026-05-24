"""Tests for portwatch.metrics_hooks."""
import pytest

from portwatch.metrics import reset_metrics, get_metrics
from portwatch.metrics_hooks import timed_scan, record_cycle_complete, metrics_summary
from portwatch.scanner import PortState


@pytest.fixture(autouse=True)
def _reset():
    reset_metrics()
    yield
    reset_metrics()


def _make_state(port: int, status: str = "open") -> PortState:
    return PortState(host="127.0.0.1", port=port, protocol="tcp", status=status)


class TestTimedScan:
    def test_records_open_count(self):
        with timed_scan("127.0.0.1") as ctx:
            ctx["states"] = [_make_state(80), _make_state(443), _make_state(22, "closed")]
        store = get_metrics()
        assert len(store._scans) == 1
        assert store._scans[0].open_count == 2
        assert store._scans[0].port_count == 3

    def test_records_host(self):
        with timed_scan("10.0.0.1") as ctx:
            ctx["states"] = []
        assert get_metrics()._scans[0].host == "10.0.0.1"

    def test_records_error_on_exception(self):
        with pytest.raises(RuntimeError):
            with timed_scan("host") as ctx:
                raise RuntimeError("boom")
        assert get_metrics()._scans[0].error == "boom"

    def test_duration_is_positive(self):
        with timed_scan("host") as ctx:
            ctx["states"] = []
        assert get_metrics()._scans[0].duration_seconds >= 0.0

    def test_empty_states_defaults(self):
        with timed_scan("host"):
            pass  # ctx not used
        m = get_metrics()._scans[0]
        assert m.port_count == 0
        assert m.open_count == 0


class TestRecordCycleComplete:
    def test_increments_cycle_count(self):
        record_cycle_complete()
        record_cycle_complete()
        assert get_metrics().cycle_count == 2


class TestMetricsSummary:
    def test_returns_dict_with_expected_keys(self):
        summary = metrics_summary()
        assert isinstance(summary, dict)
        assert "cycle_count" in summary
        assert "total_scans" in summary

    def test_reflects_recorded_data(self):
        with timed_scan("h") as ctx:
            ctx["states"] = [_make_state(80)]
        record_cycle_complete()
        s = metrics_summary()
        assert s["total_scans"] == 1
        assert s["cycle_count"] == 1
