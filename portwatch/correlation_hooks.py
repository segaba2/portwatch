"""Thin integration layer: correlate changes produced during a scan cycle."""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from portwatch.alerts import PortChange
from portwatch.correlation import CorrelationResult, correlate_changes

logger = logging.getLogger(__name__)

# Module-level cache so callers can retrieve the last result without re-running.
_last_result: Optional[CorrelationResult] = None


def get_last_result() -> Optional[CorrelationResult]:
    """Return the CorrelationResult from the most recent :func:`run_correlation` call."""
    return _last_result


def reset() -> None:
    """Clear the cached result (useful in tests)."""
    global _last_result
    _last_result = None


def run_correlation(changes: Sequence[PortChange]) -> CorrelationResult:
    """Correlate *changes*, cache the result, and emit log warnings for
    any widespread groups detected.

    Args:
        changes: All PortChange objects from the current scan cycle.

    Returns:
        The resulting :class:`~portwatch.correlation.CorrelationResult`.
    """
    global _last_result

    result = correlate_changes(changes)
    _last_result = result

    for group in result.widespread_groups:
        logger.warning(
            "Widespread port change detected: port %d %s on %d hosts: %s",
            group.port,
            group.change_type,
            len(group.hosts),
            ", ".join(sorted(group.hosts)),
        )

    if not result.has_widespread:
        logger.debug("Correlation found no widespread changes in %d change(s).", len(changes))

    return result


def widespread_summary(result: Optional[CorrelationResult] = None) -> List[str]:
    """Return human-readable lines describing widespread groups.

    Args:
        result: A :class:`~portwatch.correlation.CorrelationResult` to
            summarise.  Defaults to :func:`get_last_result`.

    Returns:
        A list of strings, one per widespread group.  Empty when there are
        no widespread changes.
    """
    r = result or _last_result
    if r is None:
        return []

    lines: List[str] = []
    for g in r.widespread_groups:
        hosts_str = ", ".join(sorted(g.hosts))
        lines.append(
            f"Port {g.port} {g.change_type} on {len(g.hosts)} hosts: {hosts_str}"
        )
    return lines
