"""Convenience helpers that record standard audit events during a portwatch run."""

from __future__ import annotations

from typing import List, Optional

from portwatch.audit_log import AuditEntry, append_audit
from portwatch.alerts import PortChange


def record_scan_start(host: str, data_dir: str = "data") -> None:
    """Record that a scan has started for *host*."""
    append_audit(
        AuditEntry(event="scan_start", host=host, detail="port scan initiated"),
        data_dir=data_dir,
    )


def record_scan_complete(
    host: str, port_count: int, data_dir: str = "data"
) -> None:
    """Record a successful scan completion."""
    append_audit(
        AuditEntry(
            event="scan_complete",
            host=host,
            detail=f"{port_count} port(s) scanned",
        ),
        data_dir=data_dir,
    )


def record_scan_error(host: str, error: str, data_dir: str = "data") -> None:
    """Record a scan failure."""
    append_audit(
        AuditEntry(event="scan_error", host=host, detail=error),
        data_dir=data_dir,
    )


def record_changes(
    host: str, changes: List[PortChange], data_dir: str = "data"
) -> None:
    """Record each individual port change detected for *host*."""
    for change in changes:
        append_audit(
            AuditEntry(
                event="port_change",
                host=host,
                detail=change.summary(),
            ),
            data_dir=data_dir,
        )


def record_alert_sent(
    host: str, channel: str, success: bool, data_dir: str = "data"
) -> None:
    """Record the outcome of an alert dispatch."""
    status = "ok" if success else "failed"
    append_audit(
        AuditEntry(
            event="alert_sent",
            host=host,
            detail=f"channel={channel} status={status}",
        ),
        data_dir=data_dir,
    )
