"""Port filtering utilities for portwatch.

Provides functions to filter PortState lists based on various criteria
such as port ranges, protocols, and service names.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from portwatch.scanner import PortState


def filter_by_ports(
    states: Iterable[PortState],
    ports: Iterable[int],
) -> List[PortState]:
    """Return only states whose port number is in *ports*."""
    allowed = set(ports)
    return [s for s in states if s.port in allowed]


def filter_by_protocol(
    states: Iterable[PortState],
    protocol: str,
) -> List[PortState]:
    """Return only states matching *protocol* (case-insensitive)."""
    proto = protocol.lower()
    return [s for s in states if s.protocol.lower() == proto]


def filter_by_service(
    states: Iterable[PortState],
    service: str,
) -> List[PortState]:
    """Return only states whose resolved service name contains *service*."""
    needle = service.lower()
    return [
        s for s in states
        if s.service is not None and needle in s.service.lower()
    ]


def filter_open(states: Iterable[PortState]) -> List[PortState]:
    """Return only states where the port is open."""
    return [s for s in states if s.is_open]


def filter_closed(states: Iterable[PortState]) -> List[PortState]:
    """Return only states where the port is closed."""
    return [s for s in states if not s.is_open]


def apply_filters(
    states: Iterable[PortState],
    *,
    ports: Optional[Iterable[int]] = None,
    protocol: Optional[str] = None,
    service: Optional[str] = None,
    only_open: bool = False,
    only_closed: bool = False,
) -> List[PortState]:
    """Apply multiple optional filters in sequence.

    Parameters
    ----------
    states:      Iterable of PortState objects to filter.
    ports:       Restrict to this set of port numbers.
    protocol:    Restrict to this protocol string (e.g. ``"tcp"``).
    service:     Restrict to states whose service name contains this substring.
    only_open:   If True, keep only open ports.
    only_closed: If True, keep only closed ports.
    """
    result: List[PortState] = list(states)
    if ports is not None:
        result = filter_by_ports(result, ports)
    if protocol is not None:
        result = filter_by_protocol(result, protocol)
    if service is not None:
        result = filter_by_service(result, service)
    if only_open:
        result = filter_open(result)
    if only_closed:
        result = filter_closed(result)
    return result
