"""Healthcheck endpoint support for the portwatch daemon."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthStatus:
    """Represents the current health of the portwatch daemon."""

    status: str  # "ok" | "degraded" | "error"
    last_scan_ts: Optional[float] = None
    last_scan_host_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0.0
    scan_count: int = 0
    _started_at: float = field(default_factory=time.time, repr=False, compare=False)

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "last_scan_ts": self.last_scan_ts,
            "last_scan_host_count": self.last_scan_host_count,
            "last_error": self.last_error,
            "uptime_seconds": round(time.time() - self._started_at, 2),
            "scan_count": self.scan_count,
        }

    def as_json(self) -> str:
        return json.dumps(self.as_dict())


_global_status: Optional[HealthStatus] = None


def init_health() -> HealthStatus:
    """Initialise (or reset) the global health status object."""
    global _global_status
    _global_status = HealthStatus(status="ok")
    return _global_status


def get_health() -> HealthStatus:
    """Return the current global health status, creating one if needed."""
    global _global_status
    if _global_status is None:
        _global_status = HealthStatus(status="ok")
    return _global_status


def record_scan_ok(host_count: int) -> None:
    """Update health after a successful scan cycle."""
    h = get_health()
    h.status = "ok"
    h.last_scan_ts = time.time()
    h.last_scan_host_count = host_count
    h.last_error = None
    h.scan_count += 1


def record_scan_error(error: str) -> None:
    """Update health after a failed scan cycle."""
    h = get_health()
    h.status = "degraded"
    h.last_error = error
    h.scan_count += 1
