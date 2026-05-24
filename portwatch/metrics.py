"""Runtime metrics collection for portwatch daemon."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScanMetrics:
    """Metrics captured during a single scan cycle."""
    host: str
    port_count: int
    open_count: int
    duration_seconds: float
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port_count": self.port_count,
            "open_count": self.open_count,
            "duration_seconds": round(self.duration_seconds, 4),
            "error": self.error,
        }


@dataclass
class MetricsStore:
    """Accumulates metrics across scan cycles."""
    _scans: List[ScanMetrics] = field(default_factory=list)
    _cycle_count: int = 0
    _total_duration: float = 0.0
    _error_count: int = 0

    def record(self, m: ScanMetrics) -> None:
        self._scans.append(m)
        self._total_duration += m.duration_seconds
        if m.error:
            self._error_count += 1

    def increment_cycle(self) -> None:
        self._cycle_count += 1

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def average_scan_duration(self) -> float:
        if not self._scans:
            return 0.0
        return self._total_duration / len(self._scans)

    def per_host_summary(self) -> Dict[str, dict]:
        summary: Dict[str, List[ScanMetrics]] = {}
        for s in self._scans:
            summary.setdefault(s.host, []).append(s)
        result = {}
        for host, entries in summary.items():
            durations = [e.duration_seconds for e in entries]
            result[host] = {
                "scans": len(entries),
                "avg_duration": round(sum(durations) / len(durations), 4),
                "errors": sum(1 for e in entries if e.error),
            }
        return result

    def as_dict(self) -> dict:
        return {
            "cycle_count": self._cycle_count,
            "total_scans": len(self._scans),
            "error_count": self._error_count,
            "average_scan_duration": round(self.average_scan_duration, 4),
            "per_host": self.per_host_summary(),
        }


_store = MetricsStore()


def get_metrics() -> MetricsStore:
    return _store


def reset_metrics() -> None:
    global _store
    _store = MetricsStore()
