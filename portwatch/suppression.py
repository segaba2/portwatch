"""Alert suppression rules — skip notifications for known/expected ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from portwatch.alerts import PortChange


@dataclass
class SuppressionRule:
    """A single suppression rule matching host, port, and optional protocol."""

    host: str
    port: int
    protocol: str = "tcp"  # tcp | udp | *

    def matches(self, change: PortChange) -> bool:
        host_match = self.host in ("*", change.host)
        port_match = self.port == change.port
        proto_match = self.protocol in ("*", change.protocol)
        return host_match and port_match and proto_match

    def as_dict(self) -> dict:
        return {"host": self.host, "port": self.port, "protocol": self.protocol}

    @classmethod
    def from_dict(cls, data: dict) -> "SuppressionRule":
        return cls(
            host=data["host"],
            port=int(data["port"]),
            protocol=data.get("protocol", "tcp"),
        )


@dataclass
class SuppressionList:
    """Collection of suppression rules."""

    rules: list[SuppressionRule] = field(default_factory=list)

    def is_suppressed(self, change: PortChange) -> bool:
        """Return True if *any* rule matches the change."""
        return any(rule.matches(change) for rule in self.rules)

    def filter_changes(
        self, changes: Iterable[PortChange]
    ) -> list[PortChange]:
        """Return only changes that are NOT suppressed."""
        return [c for c in changes if not self.is_suppressed(c)]

    @classmethod
    def from_list(cls, raw: list[dict]) -> "SuppressionList":
        return cls(rules=[SuppressionRule.from_dict(r) for r in raw])

    def as_list(self) -> list[dict]:
        return [r.as_dict() for r in self.rules]
