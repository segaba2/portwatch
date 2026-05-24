"""Port fingerprinting: capture and compare service banners for open ports."""
from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_TIMEOUT = 2.0
DEFAULT_BANNER_BYTES = 256


@dataclass
class Fingerprint:
    host: str
    port: int
    protocol: str
    banner: str = ""
    error: str = ""

    def as_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "banner": self.banner,
            "error": self.error,
        }

    @staticmethod
    def from_dict(d: dict) -> "Fingerprint":
        return Fingerprint(
            host=d["host"],
            port=d["port"],
            protocol=d["protocol"],
            banner=d.get("banner", ""),
            error=d.get("error", ""),
        )

    def has_changed(self, other: "Fingerprint") -> bool:
        """Return True if the banner differs from another fingerprint."""
        return self.banner != other.banner


def grab_banner(
    host: str,
    port: int,
    protocol: str = "tcp",
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_BANNER_BYTES,
) -> Fingerprint:
    """Attempt to connect and read a banner from the given host/port."""
    if protocol != "tcp":
        return Fingerprint(host=host, port=port, protocol=protocol, error="udp banner grab not supported")
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            try:
                raw = sock.recv(max_bytes)
                banner = raw.decode("utf-8", errors="replace").strip()
            except socket.timeout:
                banner = ""
        return Fingerprint(host=host, port=port, protocol=protocol, banner=banner)
    except OSError as exc:
        return Fingerprint(host=host, port=port, protocol=protocol, error=str(exc))


def fingerprint_ports(
    host: str,
    ports: list[int],
    protocol: str = "tcp",
    timeout: float = DEFAULT_TIMEOUT,
) -> list[Fingerprint]:
    """Grab banners for a list of ports on a single host."""
    return [grab_banner(host, port, protocol, timeout) for port in ports]
