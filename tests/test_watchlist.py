"""Tests for portwatch.watchlist."""

import json
import pytest
from portwatch.watchlist import (
    Watchlist,
    WatchlistEntry,
    save_watchlist,
    load_watchlist,
    load_watchlist_or_empty,
)


def _entry(host="example.com", port=80, protocol="tcp", description="") -> WatchlistEntry:
    return WatchlistEntry(host=host, port=port, protocol=protocol, description=description)


class TestWatchlistEntry:
    def test_key(self):
        e = _entry()
        assert e.key() == ("example.com", 80, "tcp")

    def test_as_dict_round_trip(self):
        e = _entry(description="web")
        assert WatchlistEntry.from_dict(e.as_dict()) == e

    def test_from_dict_defaults(self):
        e = WatchlistEntry.from_dict({"host": "h", "port": 22})
        assert e.protocol == "tcp"
        assert e.description == ""


class TestWatchlist:
    def test_add_entry(self):
        wl = Watchlist()
        wl.add(_entry())
        assert len(wl.entries) == 1

    def test_add_duplicate_ignored(self):
        wl = Watchlist()
        wl.add(_entry())
        wl.add(_entry())
        assert len(wl.entries) == 1

    def test_add_different_protocol_allowed(self):
        wl = Watchlist()
        wl.add(_entry(protocol="tcp"))
        wl.add(_entry(protocol="udp"))
        assert len(wl.entries) == 2

    def test_remove_existing(self):
        wl = Watchlist()
        wl.add(_entry())
        removed = wl.remove("example.com", 80)
        assert removed is True
        assert len(wl.entries) == 0

    def test_remove_nonexistent_returns_false(self):
        wl = Watchlist()
        assert wl.remove("missing.com", 9999) is False

    def test_contains_true(self):
        wl = Watchlist()
        wl.add(_entry())
        assert wl.contains("example.com", 80) is True

    def test_contains_false(self):
        wl = Watchlist()
        assert wl.contains("example.com", 80) is False

    def test_as_dict_round_trip(self):
        wl = Watchlist()
        wl.add(_entry(port=443, description="https"))
        wl.add(_entry(port=22, protocol="tcp"))
        restored = Watchlist.from_dict(wl.as_dict())
        assert len(restored.entries) == 2
        assert restored.contains("example.com", 443)


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        wl = Watchlist()
        wl.add(_entry(port=8080, description="alt-http"))
        save_watchlist(wl, str(tmp_path))
        loaded = load_watchlist(str(tmp_path))
        assert loaded is not None
        assert loaded.contains("example.com", 8080)

    def test_load_missing_returns_none(self, tmp_path):
        assert load_watchlist(str(tmp_path / "nodir")) is None

    def test_load_or_empty_missing(self, tmp_path):
        wl = load_watchlist_or_empty(str(tmp_path / "nodir"))
        assert isinstance(wl, Watchlist)
        assert wl.entries == []

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b"
        wl = Watchlist()
        save_watchlist(wl, str(nested))
        assert (nested / "watchlist.json").exists()

    def test_file_is_valid_json(self, tmp_path):
        wl = Watchlist()
        wl.add(_entry())
        save_watchlist(wl, str(tmp_path))
        raw = (tmp_path / "watchlist.json").read_text()
        data = json.loads(raw)
        assert "entries" in data
