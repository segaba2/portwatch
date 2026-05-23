"""Compare a live scan result against a stored baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from portwatch.baseline import Baseline
from portwatch.scanner import PortState


@dataclass
class BaselineDiffResult:
    """Ports that deviate from the stored baseline for a single host."""

    host: str
    unexpected_open: list[PortState]   # open in scan but not in baseline
    unexpected_closed: list[PortState]  # in baseline but not open in scan

    @property
    def has_deviation(self) -> bool:
        return bool(self.unexpected_open or self.unexpected_closed)

    def summary(self) -> str:
        parts = []
        if self.unexpected_open:
            ports = ", ".join(str(s.port) for s in self.unexpected_open)
            parts.append(f"+opened: {ports}")
        if self.unexpected_closed:
            ports = ", ".join(str(s.port) for s in self.unexpected_closed)
            parts.append(f"-closed: {ports}")
        return f"{self.host}: " + (" | ".join(parts) if parts else "no deviation")


def _open_ports(states: list[PortState]) -> set[tuple[int, str]]:
    return {(s.port, s.protocol) for s in states if s.open}


def diff_against_baseline(
    baseline: Baseline,
    current: dict[str, list[PortState]],
) -> list[BaselineDiffResult]:
    """Return a deviation report for every host present in *baseline* or *current*."""
    all_hosts = set(baseline.states.keys()) | set(current.keys())
    results: list[BaselineDiffResult] = []

    for host in sorted(all_hosts):
        baseline_states = baseline.states.get(host, [])
        current_states = current.get(host, [])

        baseline_open = _open_ports(baseline_states)
        current_open = _open_ports(current_states)

        current_map = {(s.port, s.protocol): s for s in current_states}
        baseline_map = {(s.port, s.protocol): s for s in baseline_states}

        unexpected_open = [
            current_map[key] for key in (current_open - baseline_open)
        ]
        unexpected_closed = [
            baseline_map[key] for key in (baseline_open - current_open)
        ]

        results.append(
            BaselineDiffResult(
                host=host,
                unexpected_open=sorted(unexpected_open, key=lambda s: s.port),
                unexpected_closed=sorted(unexpected_closed, key=lambda s: s.port),
            )
        )

    return results


def any_deviation(results: list[BaselineDiffResult]) -> bool:
    return any(r.has_deviation for r in results)
