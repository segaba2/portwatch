"""Watchlist: manage a set of (host, port) pairs that should always be monitored."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class WatchlistEntry:
    host: str
    port: int
    protocol: str = "tcp"
    description: str = ""

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchlistEntry":
        return cls(
            host=data["host"],
            port=data["port"],
            protocol=data.get("protocol", "tcp"),
            description=data.get("description", ""),
        )

    def key(self) -> Tuple[str, int, str]:
        return (self.host, self.port, self.protocol)


@dataclass
class Watchlist:
    entries: List[WatchlistEntry] = field(default_factory=list)

    def add(self, entry: WatchlistEntry) -> None:
        if entry.key() not in {e.key() for e in self.entries}:
            self.entries.append(entry)

    def remove(self, host: str, port: int, protocol: str = "tcp") -> bool:
        key = (host, port, protocol)
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.key() != key]
        return len(self.entries) < before

    def contains(self, host: str, port: int, protocol: str = "tcp") -> bool:
        return (host, port, protocol) in {e.key() for e in self.entries}

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "Watchlist":
        return cls(entries=[WatchlistEntry.from_dict(d) for d in data.get("entries", [])])


def _watchlist_path(data_dir: str) -> Path:
    return Path(data_dir) / "watchlist.json"


def save_watchlist(watchlist: Watchlist, data_dir: str) -> None:
    path = _watchlist_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(watchlist.as_dict(), indent=2))


def load_watchlist(data_dir: str) -> Optional[Watchlist]:
    path = _watchlist_path(data_dir)
    if not path.exists():
        return None
    return Watchlist.from_dict(json.loads(path.read_text()))


def load_watchlist_or_empty(data_dir: str) -> Watchlist:
    return load_watchlist(data_dir) or Watchlist()
