"""Tests for portwatch.history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portwatch.history import (
    HistoryEntry,
    append_history,
    latest_entry,
    load_history,
)
from portwatch.scanner import PortState


def _states(ports: list[int], host: str = "127.0.0.1") -> list[PortState]:
    return [PortState(host=host, port=p, status="open") for p in ports]


class TestHistoryEntry:
    def test_round_trip(self):
        entry = HistoryEntry(
            timestamp="2024-01-01T00:00:00+00:00",
            host="10.0.0.1",
            states=_states([80, 443], host="10.0.0.1"),
        )
        restored = HistoryEntry.from_dict(entry.as_dict())
        assert restored.timestamp == entry.timestamp
        assert restored.host == entry.host
        assert restored.states == entry.states

    def test_as_dict_structure(self):
        entry = HistoryEntry(
            timestamp="2024-06-01T12:00:00+00:00",
            host="host",
            states=_states([22]),
        )
        d = entry.as_dict()
        assert "timestamp" in d
        assert "host" in d
        assert isinstance(d["states"], list)
        assert d["states"][0]["port"] == 22


class TestAppendAndLoad:
    def test_empty_history_returns_empty_list(self, tmp_path):
        assert load_history(tmp_path, "192.168.1.1") == []

    def test_append_creates_file(self, tmp_path):
        append_history(tmp_path, "192.168.1.1", _states([80]))
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].suffix == ".json"

    def test_append_and_load_round_trip(self, tmp_path):
        host = "10.0.0.5"
        append_history(tmp_path, host, _states([22, 80], host=host))
        entries = load_history(tmp_path, host)
        assert len(entries) == 1
        assert entries[0].host == host
        assert len(entries[0].states) == 2

    def test_multiple_appends_accumulate(self, tmp_path):
        host = "10.0.0.5"
        for ports in ([80], [80, 443], [22, 80, 443]):
            append_history(tmp_path, host, _states(ports, host=host))
        entries = load_history(tmp_path, host)
        assert len(entries) == 3

    def test_max_entries_cap(self, tmp_path):
        host = "capped"
        for i in range(15):
            append_history(tmp_path, host, _states([i], host=host), max_entries=10)
        entries = load_history(tmp_path, host)
        assert len(entries) == 10
        # Oldest entries were dropped; last state has port == 14
        assert entries[-1].states[0].port == 14

    def test_creates_parent_dirs(self, tmp_path):
        base = tmp_path / "deep" / "nested"
        append_history(base, "host", _states([443]))
        assert base.exists()


class TestLatestEntry:
    def test_returns_none_when_no_history(self, tmp_path):
        assert latest_entry(tmp_path, "ghost") is None

    def test_returns_most_recent(self, tmp_path):
        host = "recent"
        append_history(tmp_path, host, _states([80], host=host))
        append_history(tmp_path, host, _states([80, 443], host=host))
        entry = latest_entry(tmp_path, host)
        assert entry is not None
        assert len(entry.states) == 2
