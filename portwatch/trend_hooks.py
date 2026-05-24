"""Module-level hooks for managing trend state across daemon cycles."""

from __future__ import annotations

from typing import Dict, List, Optional

from portwatch.alerts import PortChange
from portwatch.trend import TrendPoint, TrendSummary, compute_trends, record_changes

_points: List[TrendPoint] = []


def reset() -> None:
    """Clear all recorded trend points (useful for testing)."""
    global _points
    _points = []


def ingest_changes(changes: List[PortChange]) -> None:
    """Record a new batch of PortChanges into the global trend store."""
    global _points
    _points = record_changes(_points, changes)


def get_trends() -> Dict[str, TrendSummary]:
    """Return aggregated TrendSummary objects for all recorded points."""
    return compute_trends(_points)


def get_flapping() -> List[TrendSummary]:
    """Return only TrendSummary entries that are considered flapping."""
    return [s for s in get_trends().values() if s.is_flapping]


def flapping_summary() -> str:
    """Human-readable summary of currently flapping ports."""
    flapping = get_flapping()
    if not flapping:
        return "No flapping ports detected."
    lines = ["Flapping ports:"]
    for s in flapping:
        lines.append(
            f"  {s.host}:{s.port}/{s.protocol} — "
            f"{s.open_count} opens, {s.close_count} closes, "
            f"{s.flap_count} flaps (last seen {s.last_seen})"
        )
    return "\n".join(lines)


def get_point_count() -> int:
    """Return the total number of recorded trend points."""
    return len(_points)
