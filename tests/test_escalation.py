"""Tests for portwatch.escalation."""

from datetime import datetime, timezone, timedelta

import pytest

from portwatch.escalation import EscalationConfig, EscalationState, EscalationTracker


@pytest.fixture
def cfg() -> EscalationConfig:
    return EscalationConfig(enabled=True, threshold=3, cooldown_minutes=60)


@pytest.fixture
def tracker(cfg: EscalationConfig) -> EscalationTracker:
    return EscalationTracker(config=cfg)


class TestEscalationState:
    def test_as_dict_round_trip(self):
        now = datetime.now(timezone.utc)
        state = EscalationState(count=2, first_seen=now, last_seen=now, escalated=False)
        restored = EscalationState.from_dict(state.as_dict())
        assert restored.count == state.count
        assert restored.escalated == state.escalated
        assert restored.first_seen is not None

    def test_from_dict_none_timestamps(self):
        state = EscalationState.from_dict({"count": 0, "first_seen": None, "last_seen": None, "escalated": False})
        assert state.first_seen is None
        assert state.last_seen is None


class TestEscalationTracker:
    def test_first_record_not_escalated(self, tracker: EscalationTracker):
        state = tracker.record("host:80")
        assert state.count == 1
        assert not state.escalated

    def test_escalates_at_threshold(self, tracker: EscalationTracker):
        for _ in range(3):
            state = tracker.record("host:443")
        assert state.escalated
        assert tracker.is_escalated("host:443")

    def test_below_threshold_not_escalated(self, tracker: EscalationTracker):
        for _ in range(2):
            tracker.record("host:22")
        assert not tracker.is_escalated("host:22")

    def test_reset_clears_state(self, tracker: EscalationTracker):
        for _ in range(3):
            tracker.record("host:8080")
        tracker.reset("host:8080")
        assert not tracker.is_escalated("host:8080")

    def test_is_escalated_unknown_key_returns_false(self, tracker: EscalationTracker):
        assert not tracker.is_escalated("unknown:9999")

    def test_cooldown_resets_counter(self, tracker: EscalationTracker):
        # Record twice, then simulate cooldown by backdating last_seen
        tracker.record("host:25")
        tracker.record("host:25")
        state = tracker._states["host:25"]
        state.last_seen = datetime.now(timezone.utc) - timedelta(minutes=90)

        # Next record should reset count to 1
        new_state = tracker.record("host:25")
        assert new_state.count == 1
        assert not new_state.escalated

    def test_multiple_keys_are_independent(self, tracker: EscalationTracker):
        for _ in range(3):
            tracker.record("host:80")
        tracker.record("host:443")
        assert tracker.is_escalated("host:80")
        assert not tracker.is_escalated("host:443")
