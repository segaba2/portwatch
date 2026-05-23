"""Digest: aggregate multiple alerts into a single periodic summary notification."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from portwatch.alerts import PortChange


@dataclass
class DigestConfig:
    enabled: bool = False
    # How long (seconds) to accumulate changes before flushing
    window: int = 300


@dataclass
class DigestEntry:
    change: PortChange
    recorded_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {
            "host": self.change.host,
            "port": self.change.port,
            "protocol": self.change.protocol,
            "kind": self.change.kind,
            "recorded_at": self.recorded_at,
        }


@dataclass
class Digest:
    config: DigestConfig
    _entries: List[DigestEntry] = field(default_factory=list)
    _window_start: Optional[float] = field(default=None)

    def add(self, change: PortChange) -> None:
        """Add a change to the current digest window."""
        if self._window_start is None:
            self._window_start = time.time()
        self._entries.append(DigestEntry(change=change))

    def is_ready(self) -> bool:
        """Return True when the window has elapsed and there are pending entries."""
        if not self._entries or self._window_start is None:
            return False
        return (time.time() - self._window_start) >= self.config.window

    def flush(self) -> List[DigestEntry]:
        """Return accumulated entries and reset the digest."""
        entries = list(self._entries)
        self._entries.clear()
        self._window_start = None
        return entries

    def pending_count(self) -> int:
        return len(self._entries)


def build_digest_body(entries: List[DigestEntry]) -> str:
    """Build a human-readable body from a list of digest entries."""
    if not entries:
        return "No changes recorded."
    lines = [f"Portwatch digest — {len(entries)} change(s) detected:", ""]
    for e in entries:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e.recorded_at))
        lines.append(
            f"  [{ts}] {e.change.kind.upper():8s}  {e.change.host}:{e.change.port}/{e.change.protocol}"
        )
    return "\n".join(lines)
