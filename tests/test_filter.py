"""Tests for portwatch.filter."""

from __future__ import annotations

import pytest

from portwatch.scanner import PortState
from portwatch.filter import (
    apply_filters,
    filter_by_ports,
    filter_by_protocol,
    filter_by_service,
    filter_closed,
    filter_open,
)


def _s(port: int, is_open: bool = True, protocol: str = "tcp", service: str | None = None) -> PortState:
    return PortState(host="127.0.0.1", port=port, is_open=is_open, protocol=protocol, service=service)


STATES = [
    _s(22,  is_open=True,  protocol="tcp", service="ssh"),
    _s(80,  is_open=True,  protocol="tcp", service="http"),
    _s(443, is_open=True,  protocol="tcp", service="https"),
    _s(53,  is_open=True,  protocol="udp", service="domain"),
    _s(8080, is_open=False, protocol="tcp", service="http-alt"),
    _s(9999, is_open=False, protocol="tcp", service=None),
]


class TestFilterByPorts:
    def test_single_port(self):
        result = filter_by_ports(STATES, [22])
        assert len(result) == 1
        assert result[0].port == 22

    def test_multiple_ports(self):
        result = filter_by_ports(STATES, [80, 443])
        assert {s.port for s in result} == {80, 443}

    def test_no_match(self):
        assert filter_by_ports(STATES, [1234]) == []

    def test_empty_ports(self):
        assert filter_by_ports(STATES, []) == []


class TestFilterByProtocol:
    def test_tcp(self):
        result = filter_by_protocol(STATES, "tcp")
        assert all(s.protocol.lower() == "tcp" for s in result)
        assert len(result) == 5

    def test_udp(self):
        result = filter_by_protocol(STATES, "udp")
        assert len(result) == 1
        assert result[0].port == 53

    def test_case_insensitive(self):
        assert filter_by_protocol(STATES, "TCP") == filter_by_protocol(STATES, "tcp")


class TestFilterByService:
    def test_exact_service(self):
        result = filter_by_service(STATES, "ssh")
        assert len(result) == 1
        assert result[0].port == 22

    def test_partial_match(self):
        result = filter_by_service(STATES, "http")
        ports = {s.port for s in result}
        assert 80 in ports
        assert 8080 in ports

    def test_no_service_excluded(self):
        result = filter_by_service(STATES, "http")
        assert 9999 not in {s.port for s in result}


class TestFilterOpenClosed:
    def test_filter_open(self):
        result = filter_open(STATES)
        assert all(s.is_open for s in result)
        assert len(result) == 4

    def test_filter_closed(self):
        result = filter_closed(STATES)
        assert all(not s.is_open for s in result)
        assert len(result) == 2


class TestApplyFilters:
    def test_no_filters_returns_all(self):
        assert apply_filters(STATES) == list(STATES)

    def test_combined_port_and_open(self):
        result = apply_filters(STATES, ports=[22, 8080], only_open=True)
        assert len(result) == 1
        assert result[0].port == 22

    def test_protocol_and_service(self):
        result = apply_filters(STATES, protocol="tcp", service="http")
        assert all(s.protocol.lower() == "tcp" for s in result)
        assert all("http" in (s.service or "") for s in result)

    def test_only_closed(self):
        result = apply_filters(STATES, only_closed=True)
        assert all(not s.is_open for s in result)
