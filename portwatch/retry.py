"""Retry logic for transient failures in notifications and scans."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 30.0
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (OSError, TimeoutError, ConnectionError)
    )


def compute_delay(attempt: int, config: RetryConfig) -> float:
    """Return the delay in seconds before the next attempt."""
    delay = config.base_delay * (config.backoff_factor ** attempt)
    return min(delay, config.max_delay)


def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """Call *fn* with *args*/*kwargs*, retrying on retryable exceptions.

    Raises the last exception if all attempts are exhausted.
    """
    cfg = config or RetryConfig()
    last_exc: Exception | None = None

    for attempt in range(cfg.max_attempts):
        try:
            return fn(*args, **kwargs)
        except cfg.retryable_exceptions as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt + 1 >= cfg.max_attempts:
                break
            delay = compute_delay(attempt, cfg)
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %.1fs.",
                attempt + 1,
                cfg.max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)

    raise last_exc  # type: ignore[misc]
