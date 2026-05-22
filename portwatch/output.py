"""Handles writing scan reports to stdout or files in various formats."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, Optional

from portwatch.reporter import ScanReport

OutputFormat = Literal["text", "json"]


def render(report: ScanReport, fmt: OutputFormat = "text") -> str:
    """Render a report to a string in the requested format."""
    if fmt == "json":
        return report.as_json()
    return report.as_text()


def write_report(
    report: ScanReport,
    fmt: OutputFormat = "text",
    output_path: Optional[Path] = None,
) -> None:
    """Write a rendered report to *output_path* or stdout."""
    content = render(report, fmt)
    if output_path is None:
        sys.stdout.write(content + "\n")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


def report_filename(host: str, fmt: OutputFormat = "text") -> str:
    """Return a safe filename for a report given a host and format."""
    safe_host = host.replace(".", "_").replace(":", "_")
    ext = "json" if fmt == "json" else "txt"
    return f"report_{safe_host}.{ext}"
