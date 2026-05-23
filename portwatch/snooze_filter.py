"""Filter alert changes through the active snooze list."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from portwatch.alerts import PortChange
from portwatch.snooze import SnoozeList


def partition_by_snooze(
    changes: List[PortChange],
    snooze_list: SnoozeList,
    now: Optional[datetime] = None,
) -> Tuple[List[PortChange], List[PortChange]]:
    """Split *changes* into (active, snoozed) lists.

    Returns a tuple of:
      - changes that should trigger alerts (not snoozed)
      - changes that are suppressed by an active snooze entry
    """
    now = now or datetime.now(timezone.utc)
    active: List[PortChange] = []
    snoozed: List[PortChange] = []

    for change in changes:
        if snooze_list.is_snoozed(change.host, change.port, now=now):
            snoozed.append(change)
        else:
            active.append(change)

    return active, snoozed


def filter_snoozed(
    changes: List[PortChange],
    snooze_list: SnoozeList,
    now: Optional[datetime] = None,
) -> List[PortChange]:
    """Return only changes that are *not* currently snoozed."""
    active, _ = partition_by_snooze(changes, snooze_list, now=now)
    return active


def snoozed_only(
    changes: List[PortChange],
    snooze_list: SnoozeList,
    now: Optional[datetime] = None,
) -> List[PortChange]:
    """Return only changes that are currently snoozed."""
    _, snoozed = partition_by_snooze(changes, snooze_list, now=now)
    return snoozed
