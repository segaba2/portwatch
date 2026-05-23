"""Tests for portwatch.ratelimit."""

import pytest
from portwatch.ratelimit import RateLimitConfig, RateLimiter


@pytest.fixture
def cfg():
    return RateLimitConfig(max_alerts=3, window_seconds=60, cooldown_seconds=30)


@pytest.fixture
def limiter(cfg):
    return RateLimiter(config=cfg)


class TestIsAllowed:
    def test_first_alert_allowed(self, limiter):
        assert limiter.is_allowed("host-a", now=0.0) is True

    def test_within_limit_allowed(self, limiter):
        for i in range(2):
            limiter.record("host-a", now=float(i))
        assert limiter.is_allowed("host-a", now=3.0) is True

    def test_at_limit_triggers_cooldown(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=float(i))
        assert limiter.is_allowed("host-a", now=4.0) is False

    def test_cooldown_expires(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=0.0)
        # cooldown_seconds=30, so after 31s it should be allowed again
        assert limiter.is_allowed("host-a", now=31.0) is True

    def test_window_expiry_resets_count(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=float(i))
        # window_seconds=60; at t=65 all old timestamps are pruned
        # cooldown also expires at t=30, so at t=65 both clear
        assert limiter.is_allowed("host-a", now=65.0) is True

    def test_different_hosts_are_independent(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=float(i))
        assert limiter.is_allowed("host-b", now=4.0) is True


class TestRecord:
    def test_record_increments_count(self, limiter):
        limiter.record("host-a", now=0.0)
        limiter.record("host-a", now=1.0)
        assert len(limiter._timestamps["host-a"]) == 2

    def test_record_sets_suppressed_at_max(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=float(i))
        assert limiter.suppressed_until("host-a") is not None


class TestReset:
    def test_reset_clears_timestamps(self, limiter):
        limiter.record("host-a", now=0.0)
        limiter.reset("host-a")
        assert limiter._timestamps.get("host-a") is None

    def test_reset_clears_suppression(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=float(i))
        limiter.reset("host-a")
        assert limiter.suppressed_until("host-a") is None

    def test_reset_unknown_host_noop(self, limiter):
        limiter.reset("ghost")  # should not raise


class TestSuppressedUntil:
    def test_not_suppressed_returns_none(self, limiter):
        assert limiter.suppressed_until("host-a") is None

    def test_suppressed_returns_future_timestamp(self, limiter):
        for i in range(3):
            limiter.record("host-a", now=0.0)
        # suppressed_until uses time.monotonic() internally for comparison;
        # we can only verify the stored value is positive
        val = limiter._suppressed.get("host-a", 0.0)
        assert val == pytest.approx(30.0, abs=1.0)
