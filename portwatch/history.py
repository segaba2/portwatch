"""Manages scan history — stores timestamped snapshots for trend reporting."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from portwatch.scanner import PortState

_MAX_ENTRIES = 100


@dataclass
class HistoryEntry:
    timestamp: str  # ISO-8601
    host: str
    states: List[PortState]

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "host": self.host,
            "states": [asdict(s) for s in self.states],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        states = [PortState(**s) for s in data["states"]]
        return cls(timestamp=data["timestamp"], host=data["host"], states=states)


def _history_path(base_dir: Path, host: str) -> Path:
    safe = host.replace(":", "_").replace("/", "_")
    return base_dir / f"{safe}.history.json"


def append_history(
    base_dir: Path,
    host: str,
    states: List[PortState],
    max_entries: int = _MAX_ENTRIES,
) -> None:
    """Append a new snapshot to the host's history file, capping at *max_entries*."""
    path = _history_path(base_dir, host)
    entries = load_history(base_dir, host)

    entry = HistoryEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        host=host,
        states=states,
    )
    entries.append(entry)

    # Keep only the most recent entries
    if len(entries) > max_entries:
        entries = entries[-max_entries:]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump([e.as_dict() for e in entries], fh, indent=2)


def load_history(base_dir: Path, host: str) -> List[HistoryEntry]:
    """Return stored history for *host*, or an empty list if none exists."""
    path = _history_path(base_dir, host)
    if not path.exists():
        return []
    with path.open() as fh:
        raw = json.load(fh)
    return [HistoryEntry.from_dict(d) for d in raw]


def latest_entry(base_dir: Path, host: str) -> Optional[HistoryEntry]:
    """Return the most recent history entry for *host*, or None."""
    entries = load_history(base_dir, host)
    return entries[-1] if entries else None
