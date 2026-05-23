"""Baseline management: capture, compare, and promote port scan baselines."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from portwatch.scanner import PortState
from portwatch.state_store import _serialize_state, _deserialize_state


@dataclass
class Baseline:
    """A named snapshot of expected open ports for a set of hosts."""

    name: str
    created_at: datetime
    states: dict[str, list[PortState]] = field(default_factory=dict)
    description: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "states": {
                host: [_serialize_state(s) for s in port_states]
                for host, port_states in self.states.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        states = {
            host: [_deserialize_state(s) for s in port_list]
            for host, port_list in data.get("states", {}).items()
        }
        return cls(
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            description=data.get("description", ""),
            states=states,
        )


def _baseline_path(directory: Path, name: str) -> Path:
    return directory / f"{name}.baseline.json"


def save_baseline(baseline: Baseline, directory: Path) -> Path:
    """Persist a baseline to *directory*. Returns the file path written."""
    directory.mkdir(parents=True, exist_ok=True)
    path = _baseline_path(directory, baseline.name)
    path.write_text(json.dumps(baseline.as_dict(), indent=2))
    return path


def load_baseline(name: str, directory: Path) -> Optional[Baseline]:
    """Load a baseline by *name* from *directory*. Returns None if not found."""
    path = _baseline_path(directory, name)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Baseline.from_dict(data)


def list_baselines(directory: Path) -> list[str]:
    """Return names of all baselines stored in *directory*."""
    if not directory.exists():
        return []
    return [
        p.name.replace(".baseline.json", "")
        for p in sorted(directory.glob("*.baseline.json"))
    ]


def promote_to_baseline(
    name: str,
    states: dict[str, list[PortState]],
    directory: Path,
    description: str = "",
) -> Baseline:
    """Create and save a new baseline from the current *states* mapping."""
    baseline = Baseline(
        name=name,
        created_at=datetime.now(tz=timezone.utc),
        states=states,
        description=description,
    )
    save_baseline(baseline, directory)
    return baseline
