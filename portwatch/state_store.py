"""Persistent state storage for port scan results."""

import json
import os
from datetime import datetime
from typing import Optional

from portwatch.scanner import PortState

DEFAULT_STATE_FILE = "/var/lib/portwatch/state.json"


def _serialize_state(states: list[PortState]) -> list[dict]:
    return [
        {
            "port": s.port,
            "protocol": s.protocol,
            "status": s.status,
            "service": s.service,
        }
        for s in states
    ]


def _deserialize_state(data: list[dict]) -> list[PortState]:
    return [
        PortState(
            port=entry["port"],
            protocol=entry.get("protocol", "tcp"),
            status=entry["status"],
            service=entry.get("service"),
        )
        for entry in data
    ]


def save_state(states: list[PortState], path: str = DEFAULT_STATE_FILE) -> None:
    """Persist the current port states to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "ports": _serialize_state(states),
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def load_state(path: str = DEFAULT_STATE_FILE) -> Optional[list[PortState]]:
    """Load previously saved port states from a JSON file.

    Returns None if the file does not exist.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        payload = json.load(f)
    return _deserialize_state(payload.get("ports", []))


def load_timestamp(path: str = DEFAULT_STATE_FILE) -> Optional[str]:
    """Return the ISO timestamp of the last saved state, or None."""
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        payload = json.load(f)
    return payload.get("timestamp")
