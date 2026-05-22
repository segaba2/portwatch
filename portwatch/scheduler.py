"""Scheduler utilities for portwatch daemon interval management."""

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class SchedulerStats:
    """Tracks runtime statistics for the scheduler."""
    runs: int = 0
    errors: int = 0
    last_run_duration: float = 0.0
    total_duration: float = 0.0

    @property
    def average_duration(self) -> float:
        if self.runs == 0:
            return 0.0
        return self.total_duration / self.runs


def compute_next_delay(interval: float, last_duration: float, jitter: float = 0.0) -> float:
    """Compute how long to sleep before the next run.

    Subtracts the time spent in the last run so the effective cadence
    stays close to *interval* seconds.

    Args:
        interval: Desired interval between run starts in seconds.
        last_duration: How long the previous run took in seconds.
        jitter: Optional extra seconds to add (e.g. random jitter).

    Returns:
        Non-negative sleep duration in seconds.
    """
    delay = interval - last_duration + jitter
    return max(0.0, delay)


def run_scheduled(
    task: Callable[[], None],
    interval: float,
    max_runs: Optional[int] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> SchedulerStats:
    """Run *task* repeatedly at approximately *interval* seconds.

    Args:
        task: Zero-argument callable executed each cycle.
        interval: Target seconds between successive run starts.
        max_runs: Stop after this many runs (None = run forever).
        on_error: Optional callback invoked with the exception on failure.

    Returns:
        SchedulerStats populated after all runs complete.
    """
    stats = SchedulerStats()
    run = 0

    while max_runs is None or run < max_runs:
        start = time.monotonic()
        try:
            task()
        except Exception as exc:  # noqa: BLE001
            stats.errors += 1
            logger.error("Scheduled task raised an error: %s", exc)
            if on_error is not None:
                on_error(exc)
        finally:
            duration = time.monotonic() - start
            stats.last_run_duration = duration
            stats.total_duration += duration
            stats.runs += 1
            run += 1

        if max_runs is not None and run >= max_runs:
            break

        delay = compute_next_delay(interval, duration)
        logger.debug("Next run in %.2fs (interval=%.2fs, last=%.2fs)", delay, interval, duration)
        time.sleep(delay)

    return stats
