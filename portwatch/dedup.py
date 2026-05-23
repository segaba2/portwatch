"""Alert deduplication: suppress repeated alerts for the same change within a cooldown window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DedupConfig:
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes default


@dataclass
class DedupEntry:
    change_key: str
    first_seen: float
    last_alerted: float
    alert_count: int = 1

    def as_dict(self) -> dict:
        return {
            "change_key": self.change_key,
            "first_seen": self.first_seen,
            "last_alerted": self.last_alerted,
            "alert_count": self.alert_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DedupEntry":
        return cls(
            change_key=data["change_key"],
            first_seen=data["first_seen"],
            last_alerted=data["last_alerted"],
            alert_count=data.get("alert_count", 1),
        )


@dataclass
class DedupStore:
    config: DedupConfig = field(default_factory=DedupConfig)
    _entries: Dict[str, DedupEntry] = field(default_factory=dict)

    def _make_key(self, host: str, port: int, protocol: str, change_type: str) -> str:
        return f"{host}:{port}/{protocol}:{change_type}"

    def should_alert(self, host: str, port: int, protocol: str, change_type: str, now: Optional[float] = None) -> bool:
        """Return True if this change should trigger an alert (not a duplicate)."""
        if not self.config.enabled:
            return True

        now = now if now is not None else time.time()
        key = self._make_key(host, port, protocol, change_type)

        if key not in self._entries:
            self._entries[key] = DedupEntry(
                change_key=key,
                first_seen=now,
                last_alerted=now,
            )
            return True

        entry = self._entries[key]
        elapsed = now - entry.last_alerted

        if elapsed >= self.config.cooldown_seconds:
            entry.last_alerted = now
            entry.alert_count += 1
            return True

        return False

    def expire(self, now: Optional[float] = None) -> int:
        """Remove entries older than 2x cooldown. Returns number removed."""
        now = now if now is not None else time.time()
        cutoff = now - (self.config.cooldown_seconds * 2)
        before = len(self._entries)
        self._entries = {
            k: v for k, v in self._entries.items() if v.last_alerted >= cutoff
        }
        return before - len(self._entries)

    def entry_count(self) -> int:
        return len(self._entries)
