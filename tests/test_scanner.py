"""Unit tests for portwatch.scanner module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from portwatch.scanner import PortState, diff_states, scan_port, scan_ports


class TestPortState:
    def test_equality_same_port_and_status(self):
        a = PortState(port=80, is_open=True)
        b = PortState(port=80, is_open=True)
        assert a == b

    def test_inequality_different_status(self):
        a = PortState(port=80, is_open=True)
        b = PortState(port=80, is_open=False)
        assert a != b

    def test_defaults(self):
        state = PortState(port=443)
        assert state.protocol == "tcp"
        assert state.is_open is False
        assert state.service is None
        assert isinstance(state.scanned_at, datetime)


class TestScanPort:
    def test_open_port(self):
        with patch("portwatch.scanner.socket.create_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=None)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            state = scan_port("127.0.0.1", 80)
        assert state.is_open is True
        assert state.port == 80

    def test_closed_port_connection_refused(self):
        with patch(
            "portwatch.scanner.socket.create_connection",
            side_effect=ConnectionRefusedError,
        ):
            state = scan_port("127.0.0.1", 9999)
        assert state.is_open is False

    def test_closed_port_timeout(self):
        with patch(
            "portwatch.scanner.socket.create_connection",
            side_effect=TimeoutError,
        ):
            state = scan_port("127.0.0.1", 9999)
        assert state.is_open is False


class TestScanPorts:
    def test_returns_all_ports(self):
        with patch("portwatch.scanner.scan_port") as mock_scan:
            mock_scan.side_effect = lambda h, p, timeout: PortState(port=p, is_open=False)
            result = scan_ports([22, 80, 443])
        assert set(result.keys()) == {22, 80, 443}


class TestDiffStates:
    def _make(self, port: int, is_open: bool) -> PortState:
        return PortState(port=port, is_open=is_open)

    def test_newly_opened_port(self):
        prev = {80: self._make(80, False)}
        curr = {80: self._make(80, True)}
        diff = diff_states(prev, curr)
        assert len(diff["opened"]) == 1
        assert diff["opened"][0].port == 80
        assert diff["closed"] == []

    def test_newly_closed_port(self):
        prev = {443: self._make(443, True)}
        curr = {443: self._make(443, False)}
        diff = diff_states(prev, curr)
        assert diff["opened"] == []
        assert len(diff["closed"]) == 1

    def test_no_change(self):
        prev = {22: self._make(22, True)}
        curr = {22: self._make(22, True)}
        diff = diff_states(prev, curr)
        assert diff["opened"] == []
        assert diff["closed"] == []

    def test_new_port_not_in_previous(self):
        prev: dict = {}
        curr = {8080: self._make(8080, True)}
        diff = diff_states(prev, curr)
        assert len(diff["opened"]) == 1
