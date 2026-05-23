"""Tests for portwatch.audit_hooks."""

from unittest.mock import MagicMock, patch

import pytest

from portwatch.audit_hooks import (
    record_alert_sent,
    record_changes,
    record_scan_complete,
    record_scan_error,
    record_scan_start,
)
from portwatch.audit_log import load_audit


class TestRecordScanStart:
    def test_creates_entry(self, tmp_path):
        record_scan_start("10.0.0.1", data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert len(entries) == 1
        assert entries[0].event == "scan_start"
        assert entries[0].host == "10.0.0.1"


class TestRecordScanComplete:
    def test_detail_contains_port_count(self, tmp_path):
        record_scan_complete("10.0.0.2", port_count=42, data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert entries[0].event == "scan_complete"
        assert "42" in entries[0].detail


class TestRecordScanError:
    def test_error_message_stored(self, tmp_path):
        record_scan_error("host1", "connection refused", data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert entries[0].event == "scan_error"
        assert "connection refused" in entries[0].detail


class TestRecordChanges:
    def _make_change(self, summary_text: str):
        change = MagicMock()
        change.summary.return_value = summary_text
        return change

    def test_one_entry_per_change(self, tmp_path):
        changes = [
            self._make_change("port 22 opened"),
            self._make_change("port 80 closed"),
        ]
        record_changes("192.168.1.1", changes, data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert len(entries) == 2
        assert all(e.event == "port_change" for e in entries)
        assert entries[0].detail == "port 22 opened"
        assert entries[1].detail == "port 80 closed"

    def test_no_changes_writes_nothing(self, tmp_path):
        record_changes("host", [], data_dir=str(tmp_path))
        assert load_audit(data_dir=str(tmp_path)) == []


class TestRecordAlertSent:
    def test_success_status(self, tmp_path):
        record_alert_sent("host", "webhook", success=True, data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert entries[0].event == "alert_sent"
        assert "ok" in entries[0].detail
        assert "webhook" in entries[0].detail

    def test_failure_status(self, tmp_path):
        record_alert_sent("host", "email", success=False, data_dir=str(tmp_path))
        entries = load_audit(data_dir=str(tmp_path))
        assert "failed" in entries[0].detail
        assert "email" in entries[0].detail
