"""Tests for portwatch.throttle."""

import pytest
from portwatch.throttle import ThrottleConfig, Throttler


@pytest.fixture
def cfg() -> ThrottleConfig:
    return ThrottleConfig(min_interval=60.0, max_burst=3)


@pytest.fixture
def throttler(cfg: ThrottleConfig) -> Throttler:
    return Throttler(cfg)


class TestIsAllowed:
    def test_unknown_host_is_allowed(self, throttler: Throttler) -> None:
        assert throttler.is_allowed("192.168.1.1", now=0.0) is True

    def test_allowed_within_burst_limit(self, throttler: Throttler) -> None:
        t = 0.0
        throttler.record_scan("host", now=t)
        throttler.record_scan("host", now=t + 1)
        # burst_count == 2, max_burst == 3 → still allowed
        assert throttler.is_allowed("host", now=t + 2) is True

    def test_blocked_after_max_burst(self, throttler: Throttler) -> None:
        t = 0.0
        for i in range(3):
            throttler.record_scan("host", now=t + i)
        # burst_count == 3 == max_burst, interval not elapsed
        assert throttler.is_allowed("host", now=t + 5) is False

    def test_allowed_again_after_interval(self, throttler: Throttler) -> None:
        t = 0.0
        for i in range(3):
            throttler.record_scan("host", now=t + i)
        assert throttler.is_allowed("host", now=t + 61) is True


class TestRecordScan:
    def test_burst_count_increments(self, throttler: Throttler) -> None:
        t = 0.0
        throttler.record_scan("h", now=t)
        throttler.record_scan("h", now=t + 1)
        rec = throttler._record("h")
        assert rec.burst_count == 2

    def test_burst_count_resets_after_interval(self, throttler: Throttler) -> None:
        t = 0.0
        for i in range(3):
            throttler.record_scan("h", now=t + i)
        # scan again after full interval
        throttler.record_scan("h", now=t + 120)
        rec = throttler._record("h")
        assert rec.burst_count == 1

    def test_last_scan_updated(self, throttler: Throttler) -> None:
        throttler.record_scan("h", now=42.0)
        assert throttler._record("h").last_scan == 42.0


class TestSecondsUntilAllowed:
    def test_zero_when_allowed(self, throttler: Throttler) -> None:
        assert throttler.seconds_until_allowed("h", now=0.0) == 0.0

    def test_positive_when_blocked(self, throttler: Throttler) -> None:
        t = 0.0
        for i in range(3):
            throttler.record_scan("h", now=t + i)
        wait = throttler.seconds_until_allowed("h", now=t + 5)
        assert wait > 0.0
        assert wait <= 60.0

    def test_never_negative(self, throttler: Throttler) -> None:
        t = 0.0
        for i in range(3):
            throttler.record_scan("h", now=t + i)
        wait = throttler.seconds_until_allowed("h", now=t + 999)
        assert wait == 0.0


class TestReset:
    def test_reset_clears_record(self, throttler: Throttler) -> None:
        throttler.record_scan("h", now=0.0)
        throttler.reset("h")
        assert "h" not in throttler._records

    def test_reset_unknown_host_is_safe(self, throttler: Throttler) -> None:
        throttler.reset("nonexistent")  # should not raise
