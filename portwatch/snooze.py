"""Snooze: temporarily silence alerts for a host/port combination."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class SnoozeEntry:
    host: str
    port: int
    until: datetime
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if the snooze is still in effect."""
        now = now or datetime.now(timezone.utc)
        return now < self.until

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "until": self.until.isoformat(),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnoozeEntry":
        return cls(
            host=data["host"],
            port=data["port"],
            until=datetime.fromisoformat(data["until"]),
            reason=data.get("reason", ""),
        )


@dataclass
class SnoozeList:
    entries: List[SnoozeEntry] = field(default_factory=list)

    def add(self, entry: SnoozeEntry) -> None:
        self.entries.append(entry)

    def is_snoozed(self, host: str, port: int, now: Optional[datetime] = None) -> bool:
        """Return True if the given host/port pair has an active snooze."""
        return any(
            e.host == host and e.port == port and e.is_active(now)
            for e in self.entries
        )

    def purge_expired(self, now: Optional[datetime] = None) -> int:
        """Remove expired entries. Returns the number removed."""
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.is_active(now)]
        return before - len(self.entries)


def _snooze_path(data_dir: Path) -> Path:
    return data_dir / "snooze.json"


def save_snooze(snooze_list: SnoozeList, data_dir: Path) -> None:
    path = _snooze_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump([e.as_dict() for e in snooze_list.entries], fh, indent=2)


def load_snooze(data_dir: Path) -> SnoozeList:
    path = _snooze_path(data_dir)
    if not path.exists():
        return SnoozeList()
    with path.open() as fh:
        raw = json.load(fh)
    return SnoozeList(entries=[SnoozeEntry.from_dict(d) for d in raw])
