"""Severity classification for port change alerts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from portwatch.alerts import PortChange


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Well-known ports that warrant higher severity when unexpectedly opened.
_CRITICAL_PORTS = {22, 23, 3389, 5900}  # SSH, Telnet, RDP, VNC
_HIGH_PORTS = {21, 25, 110, 143, 445, 1433, 3306, 5432, 6379, 27017}


@dataclass
class SeverityResult:
    change: PortChange
    level: SeverityLevel
    reason: str

    def as_dict(self) -> Dict:
        return {
            "host": self.change.host,
            "port": self.change.port,
            "protocol": self.change.protocol,
            "kind": self.change.kind,
            "severity": self.level.value,
            "reason": self.reason,
        }


def classify(change: PortChange) -> SeverityResult:
    """Assign a severity level to a single PortChange."""
    port = change.port
    kind = change.kind  # "opened" | "closed"

    if kind == "opened":
        if port in _CRITICAL_PORTS:
            return SeverityResult(
                change, SeverityLevel.CRITICAL,
                f"Port {port} is a high-risk service (SSH/Telnet/RDP/VNC)"
            )
        if port in _HIGH_PORTS:
            return SeverityResult(
                change, SeverityLevel.HIGH,
                f"Port {port} is a sensitive service"
            )
        if port < 1024:
            return SeverityResult(
                change, SeverityLevel.MEDIUM,
                f"Port {port} is a privileged (well-known) port"
            )
        return SeverityResult(
            change, SeverityLevel.LOW,
            f"Unprivileged port {port} newly opened"
        )
    else:
        # Closed ports are generally informational unless they were critical.
        if port in _CRITICAL_PORTS or port in _HIGH_PORTS:
            return SeverityResult(
                change, SeverityLevel.MEDIUM,
                f"Sensitive port {port} is no longer open"
            )
        return SeverityResult(
            change, SeverityLevel.INFO,
            f"Port {port} closed"
        )


def classify_all(changes: List[PortChange]) -> List[SeverityResult]:
    """Classify a list of changes, returning results sorted by severity."""
    _order = [
        SeverityLevel.CRITICAL,
        SeverityLevel.HIGH,
        SeverityLevel.MEDIUM,
        SeverityLevel.LOW,
        SeverityLevel.INFO,
    ]
    results = [classify(c) for c in changes]
    results.sort(key=lambda r: _order.index(r.level))
    return results


def highest_severity(results: List[SeverityResult]) -> Optional[SeverityLevel]:
    """Return the most severe level present, or None if the list is empty."""
    if not results:
        return None
    _order = [
        SeverityLevel.CRITICAL,
        SeverityLevel.HIGH,
        SeverityLevel.MEDIUM,
        SeverityLevel.LOW,
        SeverityLevel.INFO,
    ]
    for level in _order:
        if any(r.level == level for r in results):
            return level
    return None
