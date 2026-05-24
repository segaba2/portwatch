"""Built-in example plugins shipped with portwatch."""

from __future__ import annotations

import logging
from typing import List

from portwatch.alerts import PortChange
from portwatch.plugin import Plugin, PluginMeta, register_plugin
from portwatch.scanner import PortState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Logging plugin — writes scan lifecycle events to the Python logger
# ---------------------------------------------------------------------------

def _log_scan_start(host: str, ports: List[int]) -> None:
    logger.debug("[portwatch] scan starting: host=%s ports=%d", host, len(ports))


def _log_scan_complete(host: str, states: List[PortState]) -> None:
    open_count = sum(1 for s in states if s.is_open)
    logger.info("[portwatch] scan complete: host=%s open=%d", host, open_count)


def _log_changes(host: str, changes: List[PortChange]) -> None:
    for change in changes:
        logger.warning("[portwatch] change detected: host=%s %s", host, change.summary())


def _log_error(host: str, error: Exception) -> None:
    logger.error("[portwatch] scan error: host=%s error=%s", host, error)


LOGGING_PLUGIN = Plugin(
    meta=PluginMeta(
        name="logging",
        version="1.0.0",
        description="Logs scan lifecycle events via Python logging.",
        author="portwatch",
    ),
    on_scan_start=_log_scan_start,
    on_scan_complete=_log_scan_complete,
    on_changes_detected=_log_changes,
    on_error=_log_error,
)


def register_builtin_plugins() -> None:
    """Register all built-in plugins. Safe to call multiple times."""
    try:
        register_plugin(LOGGING_PLUGIN)
    except ValueError:
        pass  # already registered
