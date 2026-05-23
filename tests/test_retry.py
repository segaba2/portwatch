"""Tests for portwatch.retry."""

import pytest
from unittest.mock import MagicMock, call, patch

from portwatch.retry import RetryConfig, compute_delay, with_retry


# ---------------------------------------------------------------------------
# RetryConfig defaults
# ---------------------------------------------------------------------------

class TestRetryConfig:
    def test_defaults(self):
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.base_delay == 1.0
        assert cfg.backoff_factor == 2.0
        assert cfg.max_delay == 30.0

    def test_custom_values(self):
        cfg = RetryConfig(max_attempts=5, base_delay=0.5)
        assert cfg.max_attempts == 5
        assert cfg.base_delay == 0.5


# ---------------------------------------------------------------------------
# compute_delay
# ---------------------------------------------------------------------------

class TestComputeDelay:
    def test_first_attempt(self):
        cfg = RetryConfig(base_delay=1.0, backoff_factor=2.0)
        assert compute_delay(0, cfg) == 1.0

    def test_second_attempt(self):
        cfg = RetryConfig(base_delay=1.0, backoff_factor=2.0)
        assert compute_delay(1, cfg) == 2.0

    def test_capped_by_max_delay(self):
        cfg = RetryConfig(base_delay=10.0, backoff_factor=5.0, max_delay=30.0)
        assert compute_delay(3, cfg) == 30.0


# ---------------------------------------------------------------------------
# with_retry
# ---------------------------------------------------------------------------

class TestWithRetry:
    def test_success_on_first_try(self):
        fn = MagicMock(return_value=42)
        result = with_retry(fn, "a", config=RetryConfig())
        assert result == 42
        fn.assert_called_once_with("a")

    def test_retries_on_transient_error(self):
        fn = MagicMock(side_effect=[OSError("down"), OSError("down"), 99])
        cfg = RetryConfig(max_attempts=3, base_delay=0.0)
        with patch("portwatch.retry.time.sleep"):
            result = with_retry(fn, config=cfg)
        assert result == 99
        assert fn.call_count == 3

    def test_raises_after_all_attempts(self):
        fn = MagicMock(side_effect=ConnectionError("refused"))
        cfg = RetryConfig(max_attempts=3, base_delay=0.0)
        with patch("portwatch.retry.time.sleep"):
            with pytest.raises(ConnectionError, match="refused"):
                with_retry(fn, config=cfg)
        assert fn.call_count == 3

    def test_non_retryable_exception_propagates_immediately(self):
        fn = MagicMock(side_effect=ValueError("bad input"))
        cfg = RetryConfig(max_attempts=3, base_delay=0.0)
        with pytest.raises(ValueError):
            with_retry(fn, config=cfg)
        fn.assert_called_once()

    def test_sleep_called_between_attempts(self):
        fn = MagicMock(side_effect=[OSError(), 1])
        cfg = RetryConfig(max_attempts=2, base_delay=0.5, backoff_factor=1.0)
        with patch("portwatch.retry.time.sleep") as mock_sleep:
            with_retry(fn, config=cfg)
        mock_sleep.assert_called_once_with(0.5)

    def test_default_config_used_when_none_provided(self):
        fn = MagicMock(return_value="ok")
        result = with_retry(fn)
        assert result == "ok"
