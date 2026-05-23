"""Append-only audit log for portwatch scan events and alert dispatches."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    event: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    host: Optional[str] = None
    detail: Optional[str] = None

    def as_dict(self) -> dict:
        d = {"event": self.event, "timestamp": self.timestamp}
        if self.host is not None:
            d["host"] = self.host
        if self.detail is not None:
            d["detail"] = self.detail
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            event=data["event"],
            timestamp=data.get("timestamp", ""),
            host=data.get("host"),
            detail=data.get("detail"),
        )


def _audit_path(data_dir: str) -> Path:
    return Path(data_dir) / "audit.log"


def append_audit(entry: AuditEntry, data_dir: str = "data") -> None:
    path = _audit_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.as_dict()) + "\n")


def load_audit(data_dir: str = "data", limit: Optional[int] = None) -> List[AuditEntry]:
    path = _audit_path(data_dir)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(AuditEntry.from_dict(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
    if limit is not None:
        return entries[-limit:]
    return entries


def clear_audit(data_dir: str = "data") -> None:
    path = _audit_path(data_dir)
    if path.exists():
        path.unlink()
