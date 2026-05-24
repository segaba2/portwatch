"""Optional GeoIP enrichment for port states and changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class GeoInfo:
    ip: str
    country_code: str = ""
    country_name: str = ""
    city: str = ""
    asn: str = ""
    org: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "country_code": self.country_code,
            "country_name": self.country_name,
            "city": self.city,
            "asn": self.asn,
            "org": self.org,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeoInfo":
        return cls(
            ip=data.get("ip", ""),
            country_code=data.get("country_code", ""),
            country_name=data.get("country_name", ""),
            city=data.get("city", ""),
            asn=data.get("asn", ""),
            org=data.get("org", ""),
        )

    def __str__(self) -> str:
        parts = [p for p in (self.city, self.country_name) if p]
        location = ", ".join(parts) if parts else "Unknown"
        return f"{self.ip} ({location})"


# In-process cache: ip -> GeoInfo
_cache: Dict[str, GeoInfo] = {}


def _lookup_via_geoip2(ip: str) -> Optional[GeoInfo]:
    """Attempt lookup using the optional geoip2 library."""
    try:
        import geoip2.database  # type: ignore
        import geoip2.errors  # type: ignore
    except ImportError:
        return None

    import os
    db_path = os.environ.get("GEOIP_DB_PATH", "/usr/share/GeoIP/GeoLite2-City.mmdb")
    if not os.path.exists(db_path):
        return None

    try:
        with geoip2.database.Reader(db_path) as reader:
            response = reader.city(ip)
            return GeoInfo(
                ip=ip,
                country_code=response.country.iso_code or "",
                country_name=response.country.name or "",
                city=response.city.name or "",
                asn="",
                org="",
            )
    except Exception:
        return None


def lookup(ip: str) -> GeoInfo:
    """Return GeoInfo for *ip*, using cache if available."""
    if ip in _cache:
        return _cache[ip]
    result = _lookup_via_geoip2(ip) or GeoInfo(ip=ip)
    _cache[ip] = result
    return result


def reset_cache() -> None:
    """Clear the in-process geo cache (useful in tests)."""
    _cache.clear()


def enrich(host: str) -> Optional[GeoInfo]:
    """Resolve *host* to an IP (best-effort) and return GeoInfo."""
    import socket
    try:
        ip = socket.gethostbyname(host)
    except OSError:
        return None
    return lookup(ip)
