"""Configuration loading for portwatch daemon."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Config:
    """Top-level portwatch configuration."""

    # Ports / hosts to scan
    hosts: List[str] = field(default_factory=lambda: ["127.0.0.1"])
    ports: List[int] = field(default_factory=list)
    port_range: Optional[tuple[int, int]] = None  # inclusive (start, end)

    # Timing
    interval_seconds: int = 60
    scan_timeout: float = 1.0

    # State persistence
    state_file: Path = Path("/var/lib/portwatch/state.json")

    # Notifications
    webhook_url: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)

    def effective_ports(self) -> List[int]:
        """Return the combined list of ports to scan."""
        result = list(self.ports)
        if self.port_range:
            start, end = self.port_range
            result.extend(range(start, end + 1))
        return sorted(set(result))


def _parse_raw(raw: dict) -> Config:
    cfg = Config()

    scan = raw.get("scan", {})
    cfg.hosts = scan.get("hosts", cfg.hosts)
    cfg.ports = scan.get("ports", cfg.ports)
    if "port_range" in scan:
        r = scan["port_range"]
        cfg.port_range = (int(r[0]), int(r[1]))
    cfg.scan_timeout = float(scan.get("timeout", cfg.scan_timeout))

    daemon = raw.get("daemon", {})
    cfg.interval_seconds = int(daemon.get("interval_seconds", cfg.interval_seconds))
    cfg.state_file = Path(daemon.get("state_file", cfg.state_file))

    notify = raw.get("notify", {})
    cfg.webhook_url = notify.get("webhook_url", cfg.webhook_url)

    smtp = notify.get("smtp", {})
    cfg.smtp_host = smtp.get("host", cfg.smtp_host)
    cfg.smtp_port = int(smtp.get("port", cfg.smtp_port))
    cfg.smtp_user = smtp.get("user", cfg.smtp_user)
    cfg.smtp_password = smtp.get("password", cfg.smtp_password)
    cfg.email_from = smtp.get("from", cfg.email_from)
    cfg.email_to = smtp.get("to", cfg.email_to)

    return cfg


def load_config(path: Path) -> Config:
    """Load configuration from a TOML file."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    return _parse_raw(raw)


def load_config_or_default(path: Optional[Path]) -> Config:
    """Load config from *path* if provided and exists, else return defaults."""
    if path and path.exists():
        return load_config(path)
    return Config()
