"""Track port change trends over time (frequency, direction, velocity)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from portwatch.alerts import PortChange


@dataclass
class TrendPoint:
    timestamp: str
    change_type: str  # "opened" | "closed"
    port: int
    host: str
    protocol: str

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "change_type": self.change_type,
            "port": self.port,
            "host": self.host,
            "protocol": self.protocol,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TrendPoint":
        return cls(
            timestamp=d["timestamp"],
            change_type=d["change_type"],
            port=d["port"],
            host=d["host"],
            protocol=d.get("protocol", "tcp"),
        )


@dataclass
class TrendSummary:
    host: str
    port: int
    protocol: str
    open_count: int = 0
    close_count: int = 0
    flap_count: int = 0  # alternating open/close
    last_seen: Optional[str] = None

    @property
    def is_flapping(self) -> bool:
        return self.flap_count >= 2

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "open_count": self.open_count,
            "close_count": self.close_count,
            "flap_count": self.flap_count,
            "last_seen": self.last_seen,
            "is_flapping": self.is_flapping,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_changes(points: List[TrendPoint], changes: List[PortChange]) -> List[TrendPoint]:
    """Append new TrendPoints from a list of PortChanges."""
    now = _now_iso()
    for change in changes:
        points.append(
            TrendPoint(
                timestamp=now,
                change_type=change.change_type,
                port=change.port,
                host=change.host,
                protocol=change.protocol,
            )
        )
    return points


def compute_trends(points: List[TrendPoint]) -> Dict[str, TrendSummary]:
    """Aggregate TrendPoints into per-(host, port, protocol) TrendSummary objects."""
    summaries: Dict[str, TrendSummary] = {}
    grouped: Dict[str, List[TrendPoint]] = {}

    for p in points:
        key = f"{p.host}:{p.port}/{p.protocol}"
        grouped.setdefault(key, []).append(p)

    for key, pts in grouped.items():
        pts_sorted = sorted(pts, key=lambda x: x.timestamp)
        first = pts_sorted[0]
        summary = TrendSummary(host=first.host, port=first.port, protocol=first.protocol)
        prev_type: Optional[str] = None
        for pt in pts_sorted:
            if pt.change_type == "opened":
                summary.open_count += 1
            else:
                summary.close_count += 1
            if prev_type is not None and pt.change_type != prev_type:
                summary.flap_count += 1
            prev_type = pt.change_type
            summary.last_seen = pt.timestamp
        summaries[key] = summary

    return summaries
