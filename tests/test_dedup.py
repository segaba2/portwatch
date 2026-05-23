"""Tests for portwatch.dedup."""

import pytest
from portwatch.dedup import DedupConfig, DedupEntry, DedupStore


NOW = 1_700_000_000.0


@pytest.fixture
def cfg():
    return DedupConfig(enabled=True, cooldown_seconds=300)


@pytest.fixture
def store(cfg):
    return DedupStore(config=cfg)


class TestDedupEntry:
    def test_round_trip(self):
        entry = DedupEntry(
            change_key="host:80/tcp:opened",
            first_seen=NOW,
            last_alerted=NOW + 10,
            alert_count=3,
        )
        restored = DedupEntry.from_dict(entry.as_dict())
        assert restored.change_key == entry.change_key
        assert restored.first_seen == entry.first_seen
        assert restored.last_alerted == entry.last_alerted
        assert restored.alert_count == entry.alert_count

    def test_from_dict_defaults_alert_count(self):
        data = {"change_key": "x", "first_seen": NOW, "last_alerted": NOW}
        entry = DedupEntry.from_dict(data)
        assert entry.alert_count == 1


class TestDedupStore:
    def test_first_alert_always_allowed(self, store):
        assert store.should_alert("host1", 80, "tcp", "opened", now=NOW) is True

    def test_duplicate_within_cooldown_suppressed(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        result = store.should_alert("host1", 80, "tcp", "opened", now=NOW + 100)
        assert result is False

    def test_alert_allowed_after_cooldown(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        result = store.should_alert("host1", 80, "tcp", "opened", now=NOW + 301)
        assert result is True

    def test_different_ports_are_independent(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        result = store.should_alert("host1", 443, "tcp", "opened", now=NOW + 10)
        assert result is True

    def test_different_hosts_are_independent(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        result = store.should_alert("host2", 80, "tcp", "opened", now=NOW + 10)
        assert result is True

    def test_disabled_config_always_allows(self):
        store = DedupStore(config=DedupConfig(enabled=False, cooldown_seconds=300))
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        result = store.should_alert("host1", 80, "tcp", "opened", now=NOW + 1)
        assert result is True

    def test_alert_count_increments_on_new_alert(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        store.should_alert("host1", 80, "tcp", "opened", now=NOW + 400)
        key = "host1:80/tcp:opened"
        assert store._entries[key].alert_count == 2

    def test_entry_count(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        store.should_alert("host1", 443, "tcp", "opened", now=NOW)
        assert store.entry_count() == 2

    def test_expire_removes_old_entries(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        store.should_alert("host1", 443, "tcp", "opened", now=NOW)
        removed = store.expire(now=NOW + 601)
        assert removed == 2
        assert store.entry_count() == 0

    def test_expire_keeps_recent_entries(self, store):
        store.should_alert("host1", 80, "tcp", "opened", now=NOW)
        removed = store.expire(now=NOW + 400)
        assert removed == 0
        assert store.entry_count() == 1
