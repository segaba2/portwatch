"""Persist and retrieve port fingerprints to/from disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from portwatch.fingerprint import Fingerprint

_DEFAULT_DIR = Path(".portwatch")


def _fingerprint_path(data_dir: Path, host: str) -> Path:
    safe = host.replace(":", "_").replace("/", "_")
    return data_dir / "fingerprints" / f"{safe}.json"


def save_fingerprints(fingerprints: list[Fingerprint], data_dir: Path = _DEFAULT_DIR) -> None:
    """Persist fingerprints grouped by host."""
    by_host: dict[str, list[dict]] = {}
    for fp in fingerprints:
        by_host.setdefault(fp.host, []).append(fp.as_dict())
    for host, entries in by_host.items():
        path = _fingerprint_path(data_dir, host)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(entries, indent=2))


def load_fingerprints(host: str, data_dir: Path = _DEFAULT_DIR) -> Optional[list[Fingerprint]]:
    """Load previously saved fingerprints for a host, or None if absent."""
    path = _fingerprint_path(data_dir, host)
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    return [Fingerprint.from_dict(d) for d in raw]


def diff_fingerprints(
    previous: list[Fingerprint],
    current: list[Fingerprint],
) -> list[tuple[Fingerprint, Fingerprint]]:
    """Return (old, new) pairs where the banner has changed."""
    prev_map = {(fp.host, fp.port, fp.protocol): fp for fp in previous}
    changed = []
    for fp in current:
        key = (fp.host, fp.port, fp.protocol)
        if key in prev_map and prev_map[key].has_changed(fp):
            changed.append((prev_map[key], fp))
    return changed
