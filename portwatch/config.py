"""Configuration loading for portwatch."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from portwatch.suppression import SuppressionList, SuppressionRule


@dataclass
class Config:
    hosts: list[str] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    timeout: float = 1.0
    interval: int = 60
    state_dir: Path = Path("~/.portwatch")
    webhook_url: str = ""
    email_to: str = ""
    email_from: str = ""
    smtp_host: str = "localhost"
    smtp_port: int = 25
    suppression: SuppressionList = field(default_factory=SuppressionList)

    def effective_ports(self) -> list[int]:
        return sorted(set(self.ports))


def _parse_raw(raw: dict[str, Any]) -> Config:
    cfg = Config()
    cfg.hosts = raw.get("hosts", [])
    ports: list[int] = []
    for entry in raw.get("ports", []):
        if isinstance(entry, int):
            ports.append(entry)
        elif isinstance(entry, str) and "-" in entry:
            lo, hi = entry.split("-", 1)
            ports.extend(range(int(lo), int(hi) + 1))
    cfg.ports = ports
    cfg.timeout = float(raw.get("timeout", 1.0))
    cfg.interval = int(raw.get("interval", 60))
    cfg.state_dir = Path(raw.get("state_dir", "~/.portwatch")).expanduser()
    notify = raw.get("notify", {})
    cfg.webhook_url = notify.get("webhook_url", "")
    cfg.email_to = notify.get("email_to", "")
    cfg.email_from = notify.get("email_from", "")
    cfg.smtp_host = notify.get("smtp_host", "localhost")
    cfg.smtp_port = int(notify.get("smtp_port", 25))
    raw_suppress = raw.get("suppression", [])
    cfg.suppression = SuppressionList.from_list(raw_suppress)
    return cfg


def load_config(path: Path) -> Config:
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    return _parse_raw(raw)


def load_config_or_default(path: Path) -> Config:
    if path.exists():
        return load_config(path)
    return Config()
