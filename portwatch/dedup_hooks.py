"""Integration helpers: apply deduplication to a list of PortChange objects."""

from __future__ import annotations

from typing import List, Optional, Tuple

from portwatch.alerts import PortChange
from portwatch.dedup import DedupConfig, DedupStore

_store: Optional[DedupStore] = None


def get_store(config: Optional[DedupConfig] = None) -> DedupStore:
    """Return the module-level DedupStore, initialising it if needed."""
    global _store
    if _store is None:
        _store = DedupStore(config=config or DedupConfig())
    return _store


def reset_store() -> None:
    """Reset the module-level store (useful in tests)."""
    global _store
    _store = None


def partition_changes(
    changes: List[PortChange],
    store: Optional[DedupStore] = None,
    now: Optional[float] = None,
) -> Tuple[List[PortChange], List[PortChange]]:
    """Split *changes* into (to_alert, suppressed) based on dedup state.

    Args:
        changes: List of PortChange objects to evaluate.
        store:   DedupStore to use; falls back to the module-level store.
        now:     Timestamp override (useful in tests).

    Returns:
        A tuple of (alertable_changes, suppressed_changes).
    """
    if store is None:
        store = get_store()

    alertable: List[PortChange] = []
    suppressed: List[PortChange] = []

    for change in changes:
        host = change.host
        port = change.state.port
        protocol = change.state.protocol
        change_type = change.change_type

        if store.should_alert(host, port, protocol, change_type, now=now):
            alertable.append(change)
        else:
            suppressed.append(change)

    return alertable, suppressed


def filter_changes(
    changes: List[PortChange],
    store: Optional[DedupStore] = None,
    now: Optional[float] = None,
) -> List[PortChange]:
    """Return only the changes that should generate an alert."""
    alertable, _ = partition_changes(changes, store=store, now=now)
    return alertable
