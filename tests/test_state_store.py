"""Tests for portwatch.state_store."""

import json
import os
import tempfile

import pytest

from portwatch.scanner import PortState
from portwatch.state_store import (
    load_state,
    load_timestamp,
    save_state,
)


def _make_states():
    return [
        PortState(port=22, protocol="tcp", status="open", service="ssh"),
        PortState(port=80, protocol="tcp", status="open", service="http"),
        PortState(port=443, protocol="tcp", status="open", service="https"),
    ]


class TestSaveAndLoadState:
    def test_round_trip(self, tmp_path):
        path = str(tmp_path / "state.json")
        states = _make_states()
        save_state(states, path=path)
        loaded = load_state(path=path)
        assert loaded is not None
        assert len(loaded) == len(states)
        for original, restored in zip(states, loaded):
            assert restored.port == original.port
            assert restored.protocol == original.protocol
            assert restored.status == original.status
            assert restored.service == original.service

    def test_load_missing_file_returns_none(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        result = load_state(path=path)
        assert result is None

    def test_save_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "state.json")
        save_state(_make_states(), path=path)
        assert os.path.exists(path)

    def test_saved_file_is_valid_json(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_state(_make_states(), path=path)
        with open(path) as f:
            data = json.load(f)
        assert "timestamp" in data
        assert "ports" in data
        assert isinstance(data["ports"], list)

    def test_empty_state(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_state([], path=path)
        loaded = load_state(path=path)
        assert loaded == []


class TestLoadTimestamp:
    def test_returns_timestamp_string(self, tmp_path):
        path = str(tmp_path / "state.json")
        save_state(_make_states(), path=path)
        ts = load_timestamp(path=path)
        assert ts is not None
        assert "T" in ts  # ISO format sanity check

    def test_missing_file_returns_none(self, tmp_path):
        path = str(tmp_path / "no_file.json")
        assert load_timestamp(path=path) is None
