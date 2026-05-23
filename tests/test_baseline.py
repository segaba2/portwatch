"""Tests for portwatch.baseline."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from portwatch.baseline import (
    Baseline,
    list_baselines,
    load_baseline,
    promote_to_baseline,
    save_baseline,
)
from portwatch.scanner import PortState


def _make_states() -> dict[str, list[PortState]]:
    return {
        "192.168.1.1": [
            PortState(port=22, protocol="tcp", open=True, service="ssh"),
            PortState(port=80, protocol="tcp", open=True, service="http"),
        ]
    }


class TestBaselineRoundTrip:
    def test_as_dict_and_from_dict(self):
        bl = Baseline(
            name="prod",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            states=_make_states(),
            description="production baseline",
        )
        restored = Baseline.from_dict(bl.as_dict())
        assert restored.name == bl.name
        assert restored.description == bl.description
        assert restored.created_at == bl.created_at
        assert len(restored.states["192.168.1.1"]) == 2

    def test_from_dict_missing_description_defaults_empty(self):
        data = {
            "name": "test",
            "created_at": "2024-06-01T00:00:00+00:00",
            "states": {},
        }
        bl = Baseline.from_dict(data)
        assert bl.description == ""


class TestSaveAndLoad:
    def test_save_creates_file(self, tmp_path):
        bl = Baseline(
            name="alpha",
            created_at=datetime.now(tz=timezone.utc),
            states=_make_states(),
        )
        path = save_baseline(bl, tmp_path)
        assert path.exists()
        assert path.name == "alpha.baseline.json"

    def test_load_returns_none_for_missing(self, tmp_path):
        result = load_baseline("nonexistent", tmp_path)
        assert result is None

    def test_load_restores_states(self, tmp_path):
        bl = Baseline(
            name="beta",
            created_at=datetime.now(tz=timezone.utc),
            states=_make_states(),
        )
        save_baseline(bl, tmp_path)
        loaded = load_baseline("beta", tmp_path)
        assert loaded is not None
        assert loaded.name == "beta"
        assert len(loaded.states["192.168.1.1"]) == 2


class TestListBaselines:
    def test_empty_directory(self, tmp_path):
        assert list_baselines(tmp_path) == []

    def test_missing_directory(self, tmp_path):
        assert list_baselines(tmp_path / "no_such_dir") == []

    def test_lists_saved_baselines(self, tmp_path):
        for name in ("gamma", "alpha", "beta"):
            promote_to_baseline(name, {}, tmp_path)
        names = list_baselines(tmp_path)
        assert names == ["alpha", "beta", "gamma"]


class TestPromoteToBaseline:
    def test_returns_baseline_with_correct_name(self, tmp_path):
        bl = promote_to_baseline("live", _make_states(), tmp_path, description="live")
        assert bl.name == "live"
        assert bl.description == "live"

    def test_persists_to_disk(self, tmp_path):
        promote_to_baseline("saved", _make_states(), tmp_path)
        assert load_baseline("saved", tmp_path) is not None
