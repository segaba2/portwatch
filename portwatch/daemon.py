"""Main daemon loop: scan ports, compare with stored state, and alert on changes."""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from portwatch.alerts import build_alert_body, build_alert_payload, diff_states
from portwatch.notifier import NotifierConfig, notify
from portwatch.scanner import scan_ports
from portwatch.state_store import DEFAULT_STATE_FILE, load_state, save_state

logger = logging.getLogger(__name__)


@dataclass
class DaemonConfig:
    ports: list[int]
    interval: int = 60  # seconds between scans
    protocol: str = "tcp"
    state_file: str = DEFAULT_STATE_FILE
    notifier: Optional[NotifierConfig] = None
    host: str = "localhost"


def run_once(config: DaemonConfig) -> bool:
    """Run a single scan cycle. Returns True if changes were detected."""
    logger.info("Scanning %d ports on %s", len(config.ports), config.host)
    current = scan_ports(config.ports, host=config.host, protocol=config.protocol)

    previous = load_state(path=config.state_file)
    if previous is None:
        logger.info("No previous state found — saving baseline.")
        save_state(current, path=config.state_file)
        return False

    changes = diff_states(previous, current)
    if not changes:
        logger.debug("No port changes detected.")
        save_state(current, path=config.state_file)
        return False

    logger.warning("%d port change(s) detected.", len(changes))
    save_state(current, path=config.state_file)

    if config.notifier:
        payload = build_alert_payload(changes, host=config.host)
        body = build_alert_body(changes, host=config.host)
        notify(config.notifier, payload=payload, body=body)
    else:
        logger.info("No notifier configured; skipping alert.")

    return True


def run_daemon(config: DaemonConfig) -> None:
    """Block indefinitely, running scan cycles at the configured interval."""
    logger.info(
        "portwatch daemon started (interval=%ds, ports=%s)",
        config.interval,
        config.ports,
    )
    while True:
        try:
            run_once(config)
        except Exception as exc:  # pragma: no cover
            logger.error("Scan cycle failed: %s", exc, exc_info=True)
        time.sleep(config.interval)
