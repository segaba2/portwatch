"""Generates human-readable and machine-readable scan reports."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from portwatch.scanner import PortState
from portwatch.alerts import PortChange


@dataclass
class ScanReport:
    host: str
    scanned_at: datetime
    ports: List[PortState]
    changes: List[PortChange] = field(default_factory=list)
    previous_scanned_at: Optional[datetime] = None

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def open_ports(self) -> List[PortState]:
        return [p for p in self.ports if p.is_open]

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "scanned_at": self.scanned_at.isoformat(),
            "previous_scanned_at": (
                self.previous_scanned_at.isoformat()
                if self.previous_scanned_at
                else None
            ),
            "open_ports": [
                {"port": p.port, "service": p.service} for p in self.open_ports()
            ],
            "changes": [
                {
                    "port": c.port,
                    "service": c.service,
                    "kind": c.kind,
                }
                for c in self.changes
            ],
        }

    def as_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)

    def as_text(self) -> str:
        lines = [
            f"Host       : {self.host}",
            f"Scanned at : {self.scanned_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Open ports : {len(self.open_ports())}",
        ]
        for p in self.open_ports():
            svc = f" ({p.service})" if p.service else ""
            lines.append(f"  {p.port}/tcp{svc}")
        if self.has_changes():
            lines.append(f"Changes    : {len(self.changes)}")
            for c in self.changes:
                svc = f" ({c.service})" if c.service else ""
                lines.append(f"  [{c.kind.upper()}] {c.port}/tcp{svc}")
        else:
            lines.append("Changes    : none")
        return "\n".join(lines)


def build_report(
    host: str,
    ports: List[PortState],
    changes: Optional[List[PortChange]] = None,
    previous_scanned_at: Optional[datetime] = None,
) -> ScanReport:
    return ScanReport(
        host=host,
        scanned_at=datetime.now(tz=timezone.utc),
        ports=ports,
        changes=changes or [],
        previous_scanned_at=previous_scanned_at,
    )
