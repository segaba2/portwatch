"""Throttle: per-host scan throttling to prevent hammering targets."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ThrottleConfig:
    min_interval: float = 60.0  # minimum seconds between scans of the same host
    max_burst: int = 3          # max consecutive scans before enforcing interval


@dataclass
class _HostRecord:
    last_scan: float = 0.0
    burst_count: int = 0


class Throttler:
    """Tracks per-host scan timing and enforces minimum intervals."""

    def __init__(self, config: ThrottleConfig) -> None:
        self._config = config
        self._records: Dict[str, _HostRecord] = {}

    def _record(self, host: str) -> _HostRecord:
        if host not in self._records:
            self._records[host] = _HostRecord()
        return self._records[host]

    def is_allowed(self, host: str, now: Optional[float] = None) -> bool:
        """Return True if a scan of *host* is permitted right now."""
        ts = now if now is not None else time.monotonic()
        rec = self._record(host)
        elapsed = ts - rec.last_scan

        if rec.burst_count >= self._config.max_burst:
            return elapsed >= self._config.min_interval
        return True

    def record_scan(self, host: str, now: Optional[float] = None) -> None:
        """Mark that *host* was just scanned."""
        ts = now if now is not None else time.monotonic()
        rec = self._record(host)
        elapsed = ts - rec.last_scan

        if elapsed >= self._config.min_interval:
            rec.burst_count = 1
        else:
            rec.burst_count += 1

        rec.last_scan = ts

    def seconds_until_allowed(self, host: str, now: Optional[float] = None) -> float:
        """Return how many seconds until *host* may be scanned; 0 if allowed now."""
        ts = now if now is not None else time.monotonic()
        if self.is_allowed(host, now=ts):
            return 0.0
        rec = self._record(host)
        remaining = self._config.min_interval - (ts - rec.last_scan)
        return max(0.0, remaining)

    def reset(self, host: str) -> None:
        """Clear throttle state for *host*."""
        self._records.pop(host, None)
