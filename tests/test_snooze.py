"""Tests for portwatch.snooze."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from portwatch.snooze import (
    SnoozeEntry,
    SnoozeList,
    load_snooze,
    save_snooze,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_FUTURE = _NOW + timedelta(hours=2)
_PAST = _NOW - timedelta(hours=1)


def _entry(host="192.168.1.1", port=22, until=None, reason="test"):
    return SnoozeEntry(host=host, port=port, until=until or _FUTURE, reason=reason)


class TestSnoozeEntry:
    def test_is_active_when_future(self):
        e = _entry(until=_FUTURE)
        assert e.is_active(now=_NOW) is True

    def test_is_inactive_when_past(self):
        e = _entry(until=_PAST)
        assert e.is_active(now=_NOW) is False

    def test_round_trip(self):
        e = _entry(reason="maintenance")
        restored = SnoozeEntry.from_dict(e.as_dict())
        assert restored.host == e.host
        assert restored.port == e.port
        assert restored.until == e.until
        assert restored.reason == e.reason

    def test_from_dict_defaults_reason(self):
        data = {"host": "10.0.0.1", "port": 80, "until": _FUTURE.isoformat()}
        e = SnoozeEntry.from_dict(data)
        assert e.reason == ""


class TestSnoozeList:
    def test_is_snoozed_active(self):
        sl = SnoozeList(entries=[_entry(host="h1", port=443, until=_FUTURE)])
        assert sl.is_snoozed("h1", 443, now=_NOW) is True

    def test_is_snoozed_expired(self):
        sl = SnoozeList(entries=[_entry(host="h1", port=443, until=_PAST)])
        assert sl.is_snoozed("h1", 443, now=_NOW) is False

    def test_is_snoozed_different_port(self):
        sl = SnoozeList(entries=[_entry(host="h1", port=22, until=_FUTURE)])
        assert sl.is_snoozed("h1", 80, now=_NOW) is False

    def test_is_snoozed_different_host(self):
        sl = SnoozeList(entries=[_entry(host="h1", port=22, until=_FUTURE)])
        assert sl.is_snoozed("h2", 22, now=_NOW) is False

    def test_add_entry(self):
        sl = SnoozeList()
        sl.add(_entry())
        assert len(sl.entries) == 1

    def test_purge_expired_removes_old(self):
        sl = SnoozeList(entries=[
            _entry(port=22, until=_PAST),
            _entry(port=80, until=_FUTURE),
        ])
        removed = sl.purge_expired(now=_NOW)
        assert removed == 1
        assert len(sl.entries) == 1
        assert sl.entries[0].port == 80

    def test_purge_expired_none_removed(self):
        sl = SnoozeList(entries=[_entry(until=_FUTURE)])
        assert sl.purge_expired(now=_NOW) == 0


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        sl = SnoozeList(entries=[
            _entry(host="10.0.0.1", port=22, reason="patching"),
            _entry(host="10.0.0.2", port=443),
        ])
        save_snooze(sl, tmp_path)
        loaded = load_snooze(tmp_path)
        assert len(loaded.entries) == 2
        assert loaded.entries[0].host == "10.0.0.1"
        assert loaded.entries[1].port == 443

    def test_load_missing_returns_empty(self, tmp_path):
        sl = load_snooze(tmp_path / "nonexistent")
        assert sl.entries == []

    def test_save_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "deep" / "dir"
        sl = SnoozeList(entries=[_entry()])
        save_snooze(sl, nested)
        assert (nested / "snooze.json").exists()

    def test_saved_json_is_list(self, tmp_path):
        sl = SnoozeList(entries=[_entry()])
        save_snooze(sl, tmp_path)
        raw = json.loads((tmp_path / "snooze.json").read_text())
        assert isinstance(raw, list)
        assert raw[0]["host"] == "192.168.1.1"
