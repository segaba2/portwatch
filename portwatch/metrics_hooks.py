"""Hooks that integrate metrics recording into the scan lifecycle."""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator, List, Optional

from portwatch.metrics import ScanMetrics, get_metrics
from portwatch.scanner import PortState


@contextmanager
def timed_scan(host: str) -> Iterator[dict]:
    """Context manager that times a scan block and records metrics.

    Usage::

        with timed_scan("192.168.1.1") as ctx:
            states = scan_ports(...)
            ctx["states"] = states
    """
    ctx: dict = {"states": [], "error": None}
    start = time.monotonic()
    try:
        yield ctx
    except Exception as exc:  # noqa: BLE001
        ctx["error"] = str(exc)
        raise
    finally:
        duration = time.monotonic() - start
        states: List[PortState] = ctx.get("states") or []
        open_count = sum(1 for s in states if s.status == "open")
        m = ScanMetrics(
            host=host,
            port_count=len(states),
            open_count=open_count,
            duration_seconds=duration,
            error=ctx.get("error"),
        )
        get_metrics().record(m)


def record_cycle_complete() -> None:
    """Increment the global cycle counter after a full daemon cycle."""
    get_metrics().increment_cycle()


def metrics_summary() -> dict:
    """Return the current metrics snapshot as a plain dict."""
    return get_metrics().as_dict()
