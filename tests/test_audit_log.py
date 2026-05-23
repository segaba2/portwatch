"""Tests for portwatch.audit_log."""

import json
from pathlib import Path

import pytest

from portwatch.audit_log import (
    AuditEntry,
    append_audit,
    clear_audit,
    load_audit,
)


# ---------------------------------------------------------------------------
# AuditEntry unit tests
# ---------------------------------------------------------------------------


class TestAuditEntry:
    def test_as_dict_required_fields(self):
        e = AuditEntry(event="scan_complete", timestamp="2024-01-01T00:00:00+00:00")
        d = e.as_dict()
        assert d["event"] == "scan_complete"
        assert d["timestamp"] == "2024-01-01T00:00:00+00:00"
        assert "host" not in d
        assert "detail" not in d

    def test_as_dict_with_optional_fields(self):
        e = AuditEntry(
            event="alert_sent",
            timestamp="2024-01-01T00:00:00+00:00",
            host="192.168.1.1",
            detail="webhook ok",
        )
        d = e.as_dict()
        assert d["host"] == "192.168.1.1"
        assert d["detail"] == "webhook ok"

    def test_round_trip(self):
        original = AuditEntry(
            event="port_change",
            timestamp="2024-06-15T12:00:00+00:00",
            host="10.0.0.1",
            detail="port 22 opened",
        )
        restored = AuditEntry.from_dict(original.as_dict())
        assert restored.event == original.event
        assert restored.timestamp == original.timestamp
        assert restored.host == original.host
        assert restored.detail == original.detail

    def test_from_dict_missing_optionals(self):
        e = AuditEntry.from_dict({"event": "scan_start", "timestamp": "t"})
        assert e.host is None
        assert e.detail is None

    def test_default_timestamp_is_set(self):
        e = AuditEntry(event="test")
        assert e.timestamp  # non-empty


# ---------------------------------------------------------------------------
# append / load / clear integration tests
# ---------------------------------------------------------------------------


class TestAppendAndLoad:
    def test_append_creates_file(self, tmp_path):
        data_dir = str(tmp_path)
        append_audit(AuditEntry(event="test", timestamp="t"), data_dir=data_dir)
        assert (tmp_path / "audit.log").exists()

    def test_load_missing_returns_empty(self, tmp_path):
        result = load_audit(data_dir=str(tmp_path))
        assert result == []

    def test_append_and_load_multiple(self, tmp_path):
        data_dir = str(tmp_path)
        for i in range(3):
            append_audit(
                AuditEntry(event=f"event_{i}", timestamp=f"t{i}"), data_dir=data_dir
            )
        entries = load_audit(data_dir=data_dir)
        assert len(entries) == 3
        assert entries[0].event == "event_0"
        assert entries[2].event == "event_2"

    def test_load_with_limit(self, tmp_path):
        data_dir = str(tmp_path)
        for i in range(5):
            append_audit(AuditEntry(event=f"ev_{i}", timestamp="t"), data_dir=data_dir)
        entries = load_audit(data_dir=data_dir, limit=2)
        assert len(entries) == 2
        assert entries[-1].event == "ev_4"

    def test_clear_removes_file(self, tmp_path):
        data_dir = str(tmp_path)
        append_audit(AuditEntry(event="x", timestamp="t"), data_dir=data_dir)
        clear_audit(data_dir=data_dir)
        assert not (tmp_path / "audit.log").exists()

    def test_clear_nonexistent_is_noop(self, tmp_path):
        clear_audit(data_dir=str(tmp_path))  # should not raise

    def test_file_is_newline_delimited_json(self, tmp_path):
        data_dir = str(tmp_path)
        append_audit(
            AuditEntry(event="scan", timestamp="2024-01-01T00:00:00+00:00"),
            data_dir=data_dir,
        )
        lines = (tmp_path / "audit.log").read_text().strip().splitlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event"] == "scan"
