"""Tests for portwatch.plugin_hooks lifecycle dispatchers."""

from __future__ import annotations

import pytest

from portwatch.alerts import PortChange
from portwatch.plugin import Plugin, PluginMeta, register_plugin, reset_registry
from portwatch.plugin_hooks import (
    fire_alert_sent,
    fire_changes_detected,
    fire_error,
    fire_scan_complete,
    fire_scan_start,
)
from portwatch.scanner import PortState


@pytest.fixture(autouse=True)
def _clean():
    reset_registry()
    yield
    reset_registry()


def _spy_plugin(name: str, store: dict) -> Plugin:
    return Plugin(
        meta=PluginMeta(name=name),
        on_scan_start=lambda **kw: store.update({"start": kw}),
        on_scan_complete=lambda **kw: store.update({"complete": kw}),
        on_changes_detected=lambda **kw: store.update({"changes": kw}),
        on_alert_sent=lambda **kw: store.update({"alert": kw}),
        on_error=lambda **kw: store.update({"error": kw}),
    )


def _port_state(port: int, open: bool = True) -> PortState:
    return PortState(host="localhost", port=port, is_open=open, protocol="tcp")


def _port_change(port: int) -> PortChange:
    return PortChange(host="localhost", port=port, protocol="tcp", status="opened")


class TestFireScanStart:
    def test_passes_host_and_ports(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        fire_scan_start("10.0.0.1", [22, 80])
        assert store["start"]["host"] == "10.0.0.1"
        assert store["start"]["ports"] == [22, 80]


class TestFireScanComplete:
    def test_passes_states(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        states = [_port_state(80)]
        fire_scan_complete("host", states)
        assert store["complete"]["states"] == states


class TestFireChangesDetected:
    def test_fires_when_changes_present(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        fire_changes_detected("host", [_port_change(443)])
        assert "changes" in store

    def test_does_not_fire_when_empty(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        fire_changes_detected("host", [])
        assert "changes" not in store


class TestFireAlertSent:
    def test_passes_channel(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        fire_alert_sent("host", [_port_change(80)], "webhook")
        assert store["alert"]["channel"] == "webhook"


class TestFireError:
    def test_passes_exception(self):
        store: dict = {}
        register_plugin(_spy_plugin("s", store))
        err = RuntimeError("boom")
        fire_error("host", err)
        assert store["error"]["error"] is err
