"""High-level helpers that integrate EscalationTracker with the alert pipeline."""

from __future__ import annotations

from typing import List, Tuple

from portwatch.alerts import PortChange
from portwatch.escalation import EscalationConfig, EscalationState, EscalationTracker

# Module-level singleton tracker; callers may replace it for testing.
_tracker: EscalationTracker | None = None


def get_tracker(config: EscalationConfig) -> EscalationTracker:
    """Return (or lazily create) the module-level tracker."""
    global _tracker
    if _tracker is None or _tracker.config is not config:
        _tracker = EscalationTracker(config=config)
    return _tracker


def reset_tracker() -> None:
    """Reset the module-level tracker (useful in tests)."""
    global _tracker
    _tracker = None


def evaluate_changes(
    changes: List[PortChange],
    config: EscalationConfig,
) -> Tuple[List[PortChange], List[PortChange]]:
    """Partition *changes* into (normal, escalated) lists.

    Each change is recorded in the tracker.  Changes whose key has reached
    the escalation threshold are returned in the second list.
    """
    if not config.enabled:
        return changes, []

    tracker = get_tracker(config)
    normal: List[PortChange] = []
    escalated: List[PortChange] = []

    for change in changes:
        key = _change_key(change)
        state: EscalationState = tracker.record(key)
        if state.escalated:
            escalated.append(change)
        else:
            normal.append(change)

    return normal, escalated


def _change_key(change: PortChange) -> str:
    """Derive a stable string key from a PortChange for tracker lookup."""
    host = getattr(change, "host", "unknown")
    port = change.port if hasattr(change, "port") else "?"
    kind = change.kind if hasattr(change, "kind") else "change"
    return f"{host}:{port}:{kind}"
