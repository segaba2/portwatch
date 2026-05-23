"""Escalation policy: track repeated alerts and escalate after a threshold."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class EscalationConfig:
    enabled: bool = False
    threshold: int = 3          # number of consecutive alerts before escalation
    cooldown_minutes: int = 60  # minutes before resetting the counter


@dataclass
class EscalationState:
    count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    escalated: bool = False

    def as_dict(self) -> dict:
        return {
            "count": self.count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "escalated": self.escalated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EscalationState":
        return cls(
            count=data.get("count", 0),
            first_seen=datetime.fromisoformat(data["first_seen"]) if data.get("first_seen") else None,
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None,
            escalated=data.get("escalated", False),
        )


@dataclass
class EscalationTracker:
    config: EscalationConfig
    _states: Dict[str, EscalationState] = field(default_factory=dict)

    def record(self, key: str) -> EscalationState:
        """Record an alert occurrence for *key* and return the updated state."""
        now = datetime.now(timezone.utc)
        state = self._states.get(key)

        if state is None:
            state = EscalationState(count=0, first_seen=now)
            self._states[key] = state

        # Reset if cooldown has elapsed since last seen
        if state.last_seen is not None:
            elapsed = (now - state.last_seen).total_seconds() / 60
            if elapsed >= self.config.cooldown_minutes:
                state.count = 0
                state.first_seen = now
                state.escalated = False

        state.count += 1
        state.last_seen = now

        if state.count >= self.config.threshold:
            state.escalated = True

        return state

    def is_escalated(self, key: str) -> bool:
        state = self._states.get(key)
        return state.escalated if state else False

    def reset(self, key: str) -> None:
        self._states.pop(key, None)
