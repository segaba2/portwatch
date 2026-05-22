"""Build alert messages from port state change events."""

from dataclasses import dataclass
from typing import List, Tuple

from portwatch.scanner import PortState


@dataclass
class PortChange:
    """Describes a single port state transition."""
    port: int
    protocol: str
    previous_status: str
    current_status: str
    service: str = ""

    @property
    def summary(self) -> str:
        return (
            f"Port {self.port}/{self.protocol} ({self.service or 'unknown'}): "
            f"{self.previous_status} -> {self.current_status}"
        )


def diff_states(
    previous: List[PortState], current: List[PortState]
) -> List[PortChange]:
    """Compare two port state snapshots and return a list of changes."""
    prev_map = {(s.port, s.protocol): s for s in previous}
    curr_map = {(s.port, s.protocol): s for s in current}

    changes: List[PortChange] = []

    all_keys = set(prev_map) | set(curr_map)
    for key in sorted(all_keys):
        port, proto = key
        prev = prev_map.get(key)
        curr = curr_map.get(key)

        prev_status = prev.status if prev else "absent"
        curr_status = curr.status if curr else "absent"

        if prev_status != curr_status:
            changes.append(
                PortChange(
                    port=port,
                    protocol=proto,
                    previous_status=prev_status,
                    current_status=curr_status,
                    service=(curr or prev).service if (curr or prev) else "",
                )
            )
    return changes


def build_alert_payload(changes: List[PortChange], hostname: str = "") -> dict:
    """Build a structured payload suitable for webhook delivery."""
    return {
        "hostname": hostname,
        "change_count": len(changes),
        "changes": [
            {
                "port": c.port,
                "protocol": c.protocol,
                "service": c.service,
                "previous_status": c.previous_status,
                "current_status": c.current_status,
            }
            for c in changes
        ],
    }


def build_alert_body(changes: List[PortChange], hostname: str = "") -> Tuple[str, str]:
    """Return (subject, body) strings for an email alert."""
    host_label = f" on {hostname}" if hostname else ""
    subject = f"[portwatch] {len(changes)} port change(s) detected{host_label}"
    lines = [f"portwatch detected {len(changes)} change(s){host_label}:", ""]
    for change in changes:
        lines.append(f"  • {change.summary}")
    body = "\n".join(lines)
    return subject, body
