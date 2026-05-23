"""Utilities for filtering scan results against a Watchlist."""

from __future__ import annotations

from typing import List

from portwatch.scanner import PortState
from portwatch.watchlist import Watchlist, WatchlistEntry


def states_for_watchlist(states: List[PortState], watchlist: Watchlist) -> List[PortState]:
    """Return only those PortState entries that appear in the watchlist."""
    keys = {e.key() for e in watchlist.entries}
    return [s for s in states if (s.host, s.port, s.protocol) in keys]


def missing_from_scan(
    states: List[PortState], watchlist: Watchlist
) -> List[WatchlistEntry]:
    """Return watchlist entries whose host+port were not present in the scan results at all."""
    scanned_keys = {(s.host, s.port, s.protocol) for s in states}
    return [e for e in watchlist.entries if e.key() not in scanned_keys]


def unexpected_open(
    states: List[PortState], watchlist: Watchlist
) -> List[PortState]:
    """Return open ports that are NOT in the watchlist (i.e. unexpected)."""
    keys = {e.key() for e in watchlist.entries}
    return [
        s for s in states
        if s.status == "open" and (s.host, s.port, s.protocol) not in keys
    ]


def expected_closed(
    states: List[PortState], watchlist: Watchlist
) -> List[PortState]:
    """Return watchlist entries that are present in the scan but NOT open."""
    keys = {e.key() for e in watchlist.entries}
    return [
        s for s in states
        if s.status != "open" and (s.host, s.port, s.protocol) in keys
    ]
