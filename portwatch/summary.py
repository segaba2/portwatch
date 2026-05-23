"""Human-readable summary generation for scan results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from portwatch.reporter import ScanReport
from portwatch.alerts import PortChange


@dataclass
class SummaryLine:
    icon: str
    message: str

    def __str__(self) -> str:
        return f"{self.icon}  {self.message}"


def _change_lines(changes: List[PortChange]) -> List[SummaryLine]:
    lines: List[SummaryLine] = []
    for change in changes:
        if change.kind == "opened":
            icon = "[+]"
            msg = f"{change.host}:{change.port}/{change.protocol} opened ({change.service})"
        elif change.kind == "closed":
            icon = "[-]"
            msg = f"{change.host}:{change.port}/{change.protocol} closed ({change.service})"
        else:
            icon = "[~]"
            msg = f"{change.host}:{change.port}/{change.protocol} changed ({change.service})"
        lines.append(SummaryLine(icon=icon, message=msg))
    return lines


def build_summary(report: ScanReport) -> str:
    """Return a multi-line human-readable summary of a scan report."""
    lines: List[str] = []
    hosts = sorted({s.host for s in report.states})
    lines.append(f"Scan summary — {len(hosts)} host(s) scanned")
    lines.append("")

    open_ports = report.open_ports()
    lines.append(f"Open ports : {len(open_ports)}")
    lines.append(f"Changes    : {len(report.changes)}")

    if report.changes:
        lines.append("")
        lines.append("Changes detected:")
        for sl in _change_lines(report.changes):
            lines.append(f"  {sl}")
    else:
        lines.append("")
        lines.append("No changes detected.")

    return "\n".join(lines)


def build_short_summary(report: ScanReport) -> str:
    """Return a single-line summary suitable for notifications."""
    n_open = len(report.open_ports())
    n_changes = len(report.changes)
    if n_changes == 0:
        return f"portwatch: {n_open} port(s) open, no changes"
    return f"portwatch: {n_open} port(s) open, {n_changes} change(s) detected"
