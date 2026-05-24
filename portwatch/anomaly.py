"""Anomaly detection: flag ports or hosts that deviate from expected behaviour patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from portwatch.scanner import PortState
from portwatch.alerts import PortChange


@dataclass
class AnomalyRule:
    """A single rule describing what is considered anomalous."""
    host: str
    port: int
    protocol: str = "tcp"
    reason: str = ""

    def matches(self, change: PortChange) -> bool:
        host_match = self.host == "*" or self.host == change.host
        port_match = self.port == 0 or self.port == change.port
        proto_match = self.protocol == "*" or self.protocol == change.protocol
        return host_match and port_match and proto_match

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyRule":
        return cls(
            host=data.get("host", "*"),
            port=int(data.get("port", 0)),
            protocol=data.get("protocol", "tcp"),
            reason=data.get("reason", ""),
        )


@dataclass
class AnomalyResult:
    """Result of running anomaly detection over a set of changes."""
    flagged: List[tuple] = field(default_factory=list)  # (PortChange, AnomalyRule)
    clean: List[PortChange] = field(default_factory=list)

    @property
    def has_anomalies(self) -> bool:
        return len(self.flagged) > 0

    def summary(self) -> str:
        if not self.has_anomalies:
            return "No anomalies detected."
        lines = [f"Anomalies detected ({len(self.flagged)}):"]
        for change, rule in self.flagged:
            reason = f" — {rule.reason}" if rule.reason else ""
            lines.append(f"  [{change.host}:{change.port}/{change.protocol}] {change.kind}{reason}")
        return "\n".join(lines)


def detect_anomalies(
    changes: List[PortChange],
    rules: List[AnomalyRule],
) -> AnomalyResult:
    """Check each change against the list of anomaly rules."""
    result = AnomalyResult()
    for change in changes:
        matched_rule: Optional[AnomalyRule] = None
        for rule in rules:
            if rule.matches(change):
                matched_rule = rule
                break
        if matched_rule is not None:
            result.flagged.append((change, matched_rule))
        else:
            result.clean.append(change)
    return result
