"""Correlate port changes across multiple hosts to detect patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from portwatch.alerts import PortChange


@dataclass
class CorrelationGroup:
    """A set of changes that share a common port and change type."""

    port: int
    change_type: str  # "opened" | "closed"
    hosts: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "port": self.port,
            "change_type": self.change_type,
            "hosts": list(self.hosts),
            "host_count": len(self.hosts),
        }

    @property
    def is_widespread(self) -> bool:
        """True when the same change affects more than one host."""
        return len(self.hosts) > 1


@dataclass
class CorrelationResult:
    """Outcome of correlating a batch of changes."""

    groups: List[CorrelationGroup] = field(default_factory=list)

    @property
    def widespread_groups(self) -> List[CorrelationGroup]:
        return [g for g in self.groups if g.is_widespread]

    @property
    def has_widespread(self) -> bool:
        return bool(self.widespread_groups)

    def as_dict(self) -> dict:
        return {
            "groups": [g.as_dict() for g in self.groups],
            "widespread_count": len(self.widespread_groups),
        }


def correlate_changes(changes: Sequence[PortChange]) -> CorrelationResult:
    """Group *changes* by (port, change_type) across all hosts.

    Args:
        changes: Flat list of PortChange objects from one or more hosts.

    Returns:
        A CorrelationResult whose groups list every (port, change_type) pair
        that appeared in the input, together with the affected hosts.
    """
    buckets: Dict[tuple, CorrelationGroup] = {}

    for change in changes:
        key = (change.port, change.change_type)
        if key not in buckets:
            buckets[key] = CorrelationGroup(
                port=change.port,
                change_type=change.change_type,
            )
        if change.host not in buckets[key].hosts:
            buckets[key].hosts.append(change.host)

    return CorrelationResult(groups=list(buckets.values()))
