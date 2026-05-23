"""Rate limiting for notifications to avoid alert storms."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimitConfig:
    max_alerts: int = 5
    window_seconds: int = 300  # 5 minutes
    cooldown_seconds: int = 60


@dataclass
class RateLimiter:
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _timestamps: Dict[str, list] = field(default_factory=dict, repr=False)
    _suppressed: Dict[str, float] = field(default_factory=dict, repr=False)

    def _bucket(self, host: str) -> str:
        return host

    def _prune(self, key: str, now: float) -> None:
        window = self.config.window_seconds
        self._timestamps[key] = [
            t for t in self._timestamps.get(key, []) if now - t < window
        ]

    def is_allowed(self, host: str, now: Optional[float] = None) -> bool:
        """Return True if an alert for *host* is allowed right now."""
        now = now if now is not None else time.monotonic()
        key = self._bucket(host)

        cooldown_until = self._suppressed.get(key, 0.0)
        if now < cooldown_until:
            return False

        self._prune(key, now)
        count = len(self._timestamps.get(key, []))
        return count < self.config.max_alerts

    def record(self, host: str, now: Optional[float] = None) -> None:
        """Record that an alert was sent for *host*."""
        now = now if now is not None else time.monotonic()
        key = self._bucket(host)
        self._prune(key, now)
        self._timestamps.setdefault(key, []).append(now)
        if len(self._timestamps[key]) >= self.config.max_alerts:
            self._suppressed[key] = now + self.config.cooldown_seconds

    def reset(self, host: str) -> None:
        """Clear rate-limit state for *host*."""
        key = self._bucket(host)
        self._timestamps.pop(key, None)
        self._suppressed.pop(key, None)

    def suppressed_until(self, host: str) -> Optional[float]:
        """Return the monotonic timestamp until which *host* is suppressed, or None."""
        val = self._suppressed.get(self._bucket(host), 0.0)
        return val if val > time.monotonic() else None
