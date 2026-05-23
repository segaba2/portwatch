"""Tests for portwatch.digest."""

import time
from unittest.mock import patch

import pytest

from portwatch.alerts import PortChange
from portwatch.digest import (
    Digest,
    DigestConfig,
    DigestEntry,
    build_digest_body,
)


def _change(host="host1", port=80, protocol="tcp", kind="opened") -> PortChange:
    return PortChange(host=host, port=port, protocol=protocol, kind=kind)


class TestDigestEntry:
    def test_as_dict_structure(self):
        entry = DigestEntry(change=_change(), recorded_at=1_000_000.0)
        d = entry.as_dict()
        assert d["host"] == "host1"
        assert d["port"] == 80
        assert d["protocol"] == "tcp"
        assert d["kind"] == "opened"
        assert d["recorded_at"] == 1_000_000.0


class TestDigest:
    def _digest(self, window: int = 60) -> Digest:
        return Digest(config=DigestConfig(enabled=True, window=window))

    def test_starts_empty(self):
        d = self._digest()
        assert d.pending_count() == 0
        assert not d.is_ready()

    def test_add_increments_count(self):
        d = self._digest()
        d.add(_change())
        assert d.pending_count() == 1

    def test_not_ready_before_window(self):
        d = self._digest(window=300)
        d.add(_change())
        assert not d.is_ready()

    def test_ready_after_window(self):
        d = self._digest(window=10)
        with patch("portwatch.digest.time.time", return_value=1000.0):
            d.add(_change())
        with patch("portwatch.digest.time.time", return_value=1011.0):
            assert d.is_ready()

    def test_flush_returns_entries_and_resets(self):
        d = self._digest()
        d.add(_change(port=22))
        d.add(_change(port=443))
        entries = d.flush()
        assert len(entries) == 2
        assert d.pending_count() == 0
        assert not d.is_ready()

    def test_flush_empty_returns_empty_list(self):
        d = self._digest()
        assert d.flush() == []

    def test_window_start_resets_after_flush(self):
        d = self._digest(window=5)
        with patch("portwatch.digest.time.time", return_value=1000.0):
            d.add(_change())
        d.flush()
        # After flush, window_start is None — not ready even with time elapsed
        with patch("portwatch.digest.time.time", return_value=1100.0):
            assert not d.is_ready()


class TestBuildDigestBody:
    def test_empty_entries(self):
        assert build_digest_body([]) == "No changes recorded."

    def test_contains_change_info(self):
        entry = DigestEntry(change=_change(host="srv1", port=8080, kind="closed"),
                            recorded_at=0.0)
        body = build_digest_body([entry])
        assert "srv1" in body
        assert "8080" in body
        assert "CLOSED" in body

    def test_header_shows_count(self):
        entries = [DigestEntry(change=_change(port=p), recorded_at=0.0) for p in (22, 80, 443)]
        body = build_digest_body(entries)
        assert "3 change(s)" in body
