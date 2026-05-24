"""Convenience wrappers that fire plugin lifecycle events during a portwatch scan cycle."""

from __future__ import annotations

from typing import List

from portwatch.alerts import PortChange
from portwatch.plugin import dispatch
from portwatch.scanner import PortState


def fire_scan_start(host: str, ports: List[int]) -> None:
    """Notify plugins that a scan is about to begin."""
    dispatch("on_scan_start", host=host, ports=ports)


def fire_scan_complete(host: str, states: List[PortState]) -> None:
    """Notify plugins that a scan finished successfully."""
    dispatch("on_scan_complete", host=host, states=states)


def fire_changes_detected(host: str, changes: List[PortChange]) -> None:
    """Notify plugins when port changes are detected for a host."""
    if changes:
        dispatch("on_changes_detected", host=host, changes=changes)


def fire_alert_sent(host: str, changes: List[PortChange], channel: str) -> None:
    """Notify plugins after an alert has been dispatched."""
    dispatch("on_alert_sent", host=host, changes=changes, channel=channel)


def fire_error(host: str, error: Exception) -> None:
    """Notify plugins when a scan error occurs."""
    dispatch("on_error", host=host, error=error)
