"""Tests for portwatch.alerts and portwatch.notifier."""

import json
from unittest.mock import MagicMock, patch

import pytest

from portwatch.alerts import PortChange, build_alert_body, build_alert_payload, diff_states
from portwatch.notifier import NotifierConfig, send_webhook, notify
from portwatch.scanner import PortState


# ---------------------------------------------------------------------------
# diff_states
# ---------------------------------------------------------------------------

class TestDiffStates:
    def _state(self, port, status="open", proto="tcp", service=""):
        return PortState(port=port, protocol=proto, status=status, service=service)

    def test_no_change(self):
        states = [self._state(80), self._state(443)]
        assert diff_states(states, states) == []

    def test_new_port_opened(self):
        prev = [self._state(80)]
        curr = [self._state(80), self._state(8080)]
        changes = diff_states(prev, curr)
        assert len(changes) == 1
        assert changes[0].port == 8080
        assert changes[0].previous_status == "absent"
        assert changes[0].current_status == "open"

    def test_port_closed(self):
        prev = [self._state(80), self._state(22)]
        curr = [self._state(80)]
        changes = diff_states(prev, curr)
        assert len(changes) == 1
        assert changes[0].port == 22
        assert changes[0].current_status == "absent"

    def test_status_changed(self):
        prev = [self._state(80, status="open")]
        curr = [self._state(80, status="filtered")]
        changes = diff_states(prev, curr)
        assert len(changes) == 1
        assert changes[0].previous_status == "open"
        assert changes[0].current_status == "filtered"

    def test_multiple_changes(self):
        """Multiple simultaneous changes are all reported."""
        prev = [self._state(80), self._state(22), self._state(443)]
        curr = [self._state(80), self._state(8080), self._state(443, status="filtered")]
        changes = diff_states(prev, curr)
        ports_changed = {c.port for c in changes}
        assert ports_changed == {22, 8080, 443}


# ---------------------------------------------------------------------------
# build_alert_body / build_alert_payload
# ---------------------------------------------------------------------------

class TestBuildAlert:
    def _change(self, port=80):
        return PortChange(port=port, protocol="tcp", previous_status="absent",
                          current_status="open", service="http")

    def test_subject_contains_count(self):
        subject, _ = build_alert_body([self._change()], hostname="myhost")
        assert "1" in subject
        assert "myhost" in subject

    def test_body_contains_summary(self):
        _, body = build_alert_body([self._change(80)])
        assert "80" in body
        assert "absent" in body
        assert "open" in body

    def test_payload_structure(self):
        payload = build_alert_payload([self._change(443)], hostname="srv1")
        assert payload["hostname"] == "srv1"
        assert payload["change_count"] == 1
        assert payload["changes"][0]["port"] == 443


# ---------------------------------------------------------------------------
# send_webhook
# ---------------------------------------------------------------------------

class TestSendWebhook:
    def test_success(self):
