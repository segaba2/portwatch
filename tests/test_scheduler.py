"""Tests for portwatch.scheduler."""

import time
from unittest.mock import MagicMock, patch

import pytest

from portwatch.scheduler import (
    SchedulerStats,
    compute_next_delay,
    run_scheduled,
)


# ---------------------------------------------------------------------------
# SchedulerStats
# ---------------------------------------------------------------------------

class TestSchedulerStats:
    def test_defaults(self):
        s = SchedulerStats()
        assert s.runs == 0
        assert s.errors == 0
        assert s.last_run_duration == 0.0
        assert s.total_duration == 0.0

    def test_average_duration_no_runs(self):
        s = SchedulerStats()
        assert s.average_duration == 0.0

    def test_average_duration_computed(self):
        s = SchedulerStats(runs=4, total_duration=8.0)
        assert s.average_duration == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# compute_next_delay
# ---------------------------------------------------------------------------

class TestComputeNextDelay:
    def test_simple_subtraction(self):
        delay = compute_next_delay(interval=60.0, last_duration=5.0)
        assert delay == pytest.approx(55.0)

    def test_never_negative(self):
        delay = compute_next_delay(interval=10.0, last_duration=30.0)
        assert delay == 0.0

    def test_jitter_added(self):
        delay = compute_next_delay(interval=60.0, last_duration=5.0, jitter=3.0)
        assert delay == pytest.approx(58.0)

    def test_zero_interval(self):
        delay = compute_next_delay(interval=0.0, last_duration=0.0)
        assert delay == 0.0


# ---------------------------------------------------------------------------
# run_scheduled
# ---------------------------------------------------------------------------

class TestRunScheduled:
    def test_runs_correct_number_of_times(self):
        calls = []
        with patch("portwatch.scheduler.time.sleep"):
            stats = run_scheduled(lambda: calls.append(1), interval=1.0, max_runs=3)
        assert len(calls) == 3
        assert stats.runs == 3

    def test_returns_scheduler_stats(self):
        with patch("portwatch.scheduler.time.sleep"):
            stats = run_scheduled(lambda: None, interval=1.0, max_runs=2)
        assert isinstance(stats, SchedulerStats)
        assert stats.runs == 2
        assert stats.errors == 0

    def test_error_increments_error_count(self):
        def bad_task():
            raise RuntimeError("boom")

        with patch("portwatch.scheduler.time.sleep"):
            stats = run_scheduled(bad_task, interval=1.0, max_runs=3)
        assert stats.errors == 3
        assert stats.runs == 3

    def test_on_error_callback_called(self):
        errors = []

        def bad_task():
            raise ValueError("oops")

        with patch("portwatch.scheduler.time.sleep"):
            run_scheduled(bad_task, interval=1.0, max_runs=2, on_error=errors.append)

        assert len(errors) == 2
        assert all(isinstance(e, ValueError) for e in errors)

    def test_sleep_is_called_between_runs(self):
        sleep_mock = MagicMock()
        with patch("portwatch.scheduler.time.sleep", sleep_mock):
            run_scheduled(lambda: None, interval=5.0, max_runs=3)
        # sleep called between runs — 2 times for 3 runs
        assert sleep_mock.call_count == 2

    def test_total_duration_accumulates(self):
        call_count = 0

        def slow_task():
            nonlocal call_count
            call_count += 1

        with patch("portwatch.scheduler.time.sleep"):
            stats = run_scheduled(slow_task, interval=1.0, max_runs=4)

        assert stats.total_duration >= 0.0
        assert stats.runs == 4
