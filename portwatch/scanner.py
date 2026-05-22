"""Port scanner module for detecting open TCP ports on the local machine."""

import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PortState:
    """Represents the state of a single port at a point in time."""

    port: int
    protocol: str = "tcp"
    is_open: bool = False
    service: Optional[str] = None
    scanned_at: datetime = field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortState):
            return NotImplemented
        return self.port == other.port and self.is_open == other.is_open


def resolve_service(port: int) -> Optional[str]:
    """Attempt to resolve a well-known service name for the given port."""
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return None


def scan_port(host: str, port: int, timeout: float = 0.5) -> PortState:
    """Check whether a single TCP port is open on the given host."""
    state = PortState(port=port)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            state.is_open = True
            state.service = resolve_service(port)
    except (ConnectionRefusedError, TimeoutError, OSError):
        state.is_open = False
    return state


def scan_ports(
    ports: list[int],
    host: str = "127.0.0.1",
    timeout: float = 0.5,
) -> dict[int, PortState]:
    """Scan a list of ports and return a mapping of port -> PortState."""
    results: dict[int, PortState] = {}
    for port in ports:
        results[port] = scan_port(host, port, timeout=timeout)
    return results


def diff_states(
    previous: dict[int, PortState],
    current: dict[int, PortState],
) -> dict[str, list[PortState]]:
    """Compare two port-state snapshots and return opened/closed changes."""
    opened: list[PortState] = []
    closed: list[PortState] = []

    all_ports = set(previous) | set(current)
    for port in all_ports:
        prev = previous.get(port)
        curr = current.get(port)

        if curr is None:
            continue
        if prev is None and curr.is_open:
            opened.append(curr)
        elif prev is not None and not prev.is_open and curr.is_open:
            opened.append(curr)
        elif prev is not None and prev.is_open and not curr.is_open:
            closed.append(curr)

    return {"opened": opened, "closed": closed}
