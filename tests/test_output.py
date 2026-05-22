"""Tests for portwatch.output."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from portwatch.output import render, write_report, report_filename
from portwatch.reporter import ScanReport
from portwatch.scanner import PortState

UTC = timezone.utc
_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _simple_report(host: str = "10.0.0.1") -> ScanReport:
    return ScanReport(
        host=host,
        scanned_at=_NOW,
        ports=[PortState(port=22, is_open=True, service="ssh")],
    )


class TestRender:
    def test_text_format_contains_host(self):
        out = render(_simple_report(), fmt="text")
        assert "10.0.0.1" in out

    def test_json_format_is_parseable(self):
        import json
        out = render(_simple_report(), fmt="json")
        data = json.loads(out)
        assert data["host"] == "10.0.0.1"

    def test_default_format_is_text(self):
        out = render(_simple_report())
        assert "Host" in out


class TestWriteReport:
    def test_writes_to_stdout(self, capsys):
        write_report(_simple_report(), fmt="text")
        captured = capsys.readouterr()
        assert "10.0.0.1" in captured.out

    def test_writes_to_file(self, tmp_path):
        out_file = tmp_path / "reports" / "report.txt"
        write_report(_simple_report(), fmt="text", output_path=out_file)
        assert out_file.exists()
        assert "10.0.0.1" in out_file.read_text()

    def test_writes_json_to_file(self, tmp_path):
        import json
        out_file = tmp_path / "report.json"
        write_report(_simple_report(), fmt="json", output_path=out_file)
        data = json.loads(out_file.read_text())
        assert data["host"] == "10.0.0.1"

    def test_creates_parent_dirs(self, tmp_path):
        out_file = tmp_path / "a" / "b" / "c" / "report.txt"
        write_report(_simple_report(), output_path=out_file)
        assert out_file.exists()


class TestReportFilename:
    def test_text_extension(self):
        assert report_filename("10.0.0.1", "text").endswith(".txt")

    def test_json_extension(self):
        assert report_filename("10.0.0.1", "json").endswith(".json")

    def test_dots_replaced(self):
        name = report_filename("10.0.0.1")
        assert "." not in name.replace(".txt", "").replace(".json", "")

    def test_colons_replaced(self):
        name = report_filename("::1")
        assert ":" not in name
