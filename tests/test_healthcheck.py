"""Tests for portwatch.healthcheck and portwatch.healthcheck_server."""

from __future__ import annotations

import json
import time
import urllib.request

import pytest

from portwatch.healthcheck import (
    HealthStatus,
    get_health,
    init_health,
    record_scan_error,
    record_scan_ok,
)
from portwatch.healthcheck_server import start_healthcheck_server, stop_healthcheck_server


# ---------------------------------------------------------------------------
# HealthStatus unit tests
# ---------------------------------------------------------------------------


class TestHealthStatus:
    def setup_method(self):
        init_health()

    def test_initial_status_is_ok(self):
        h = get_health()
        assert h.status == "ok"

    def test_record_scan_ok_updates_fields(self):
        record_scan_ok(host_count=3)
        h = get_health()
        assert h.status == "ok"
        assert h.last_scan_host_count == 3
        assert h.last_error is None
        assert h.scan_count == 1
        assert h.last_scan_ts is not None

    def test_record_scan_error_sets_degraded(self):
        record_scan_error("timeout on 192.168.1.1")
        h = get_health()
        assert h.status == "degraded"
        assert "192.168.1.1" in (h.last_error or "")
        assert h.scan_count == 1

    def test_scan_count_increments_on_each_call(self):
        record_scan_ok(1)
        record_scan_ok(2)
        record_scan_error("boom")
        assert get_health().scan_count == 3

    def test_as_dict_contains_required_keys(self):
        d = get_health().as_dict()
        for key in ("status", "last_scan_ts", "last_scan_host_count", "last_error",
                    "uptime_seconds", "scan_count"):
            assert key in d

    def test_as_json_is_valid_json(self):
        record_scan_ok(2)
        parsed = json.loads(get_health().as_json())
        assert parsed["status"] == "ok"

    def test_uptime_is_non_negative(self):
        time.sleep(0.01)
        assert get_health().as_dict()["uptime_seconds"] >= 0


# ---------------------------------------------------------------------------
# Healthcheck HTTP server integration test
# ---------------------------------------------------------------------------


class TestHealthcheckServer:
    _PORT = 19191

    def setup_method(self):
        init_health()
        self._srv = start_healthcheck_server(host="127.0.0.1", port=self._PORT)

    def teardown_method(self):
        stop_healthcheck_server()

    def _get(self, path: str) -> tuple[int, bytes]:
        url = f"http://127.0.0.1:{self._PORT}{path}"
        try:
            with urllib.request.urlopen(url, timeout=3) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, b""

    def test_health_endpoint_returns_200(self):
        code, _ = self._get("/health")
        assert code == 200

    def test_health_response_is_json(self):
        _, body = self._get("/health")
        parsed = json.loads(body)
        assert "status" in parsed

    def test_unknown_path_returns_404(self):
        code, _ = self._get("/unknown")
        assert code == 404

    def test_health_reflects_recorded_scan(self):
        record_scan_ok(host_count=5)
        _, body = self._get("/health")
        parsed = json.loads(body)
        assert parsed["last_scan_host_count"] == 5
