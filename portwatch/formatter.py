"""Pluggable formatters that convert a ScanReport to a string."""

from __future__ import annotations

import json
from typing import Callable, Dict

from portwatch.reporter import ScanReport
from portwatch.summary import build_summary


FormatterFn = Callable[[ScanReport], str]


def _format_text(report: ScanReport) -> str:
    """Plain-text format using the human-readable summary."""
    return build_summary(report)


def _format_json(report: ScanReport) -> str:
    """JSON format derived from ScanReport.as_dict()."""
    return json.dumps(report.as_dict(), indent=2)


def _format_csv(report: ScanReport) -> str:
    """CSV format listing every port state."""
    rows = ["host,port,protocol,service,is_open"]
    for s in sorted(report.states, key=lambda x: (x.host, x.port)):
        rows.append(f"{s.host},{s.port},{s.protocol},{s.service},{s.is_open}")
    return "\n".join(rows)


_REGISTRY: Dict[str, FormatterFn] = {
    "text": _format_text,
    "json": _format_json,
    "csv": _format_csv,
}


def available_formats() -> list[str]:
    """Return the list of registered format names."""
    return list(_REGISTRY.keys())


def register_formatter(name: str, fn: FormatterFn) -> None:
    """Register a custom formatter under *name*."""
    _REGISTRY[name] = fn


def format_report(report: ScanReport, fmt: str = "text") -> str:
    """Format *report* using the formatter identified by *fmt*.

    Raises ValueError for unknown format names.
    """
    try:
        return _REGISTRY[fmt](report)
    except KeyError:
        known = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown format {fmt!r}. Known formats: {known}")
