"""Tests for fingerprint.py and fingerprint_store.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from portwatch.fingerprint import Fingerprint, fingerprint_ports, grab_banner
from portwatch.fingerprint_store import (
    diff_fingerprints,
    load_fingerprints,
    save_fingerprints,
)


# ---------------------------------------------------------------------------
# Fingerprint dataclass
# ---------------------------------------------------------------------------

class TestFingerprint:
    def test_as_dict_structure(self):
        fp = Fingerprint(host="10.0.0.1", port=22, protocol="tcp", banner="SSH-2.0")
        d = fp.as_dict()
        assert d["host"] == "10.0.0.1"
        assert d["port"] == 22
        assert d["protocol"] == "tcp"
        assert d["banner"] == "SSH-2.0"
        assert d["error"] == ""

    def test_round_trip(self):
        fp = Fingerprint(host="host", port=80, protocol="tcp", banner="HTTP", error="")
        assert Fingerprint.from_dict(fp.as_dict()) == fp

    def test_has_changed_different_banner(self):
        a = Fingerprint(host="h", port=80, protocol="tcp", banner="v1")
        b = Fingerprint(host="h", port=80, protocol="tcp", banner="v2")
        assert a.has_changed(b) is True

    def test_has_not_changed_same_banner(self):
        a = Fingerprint(host="h", port=80, protocol="tcp", banner="v1")
        b = Fingerprint(host="h", port=80, protocol="tcp", banner="v1")
        assert a.has_changed(b) is False


# ---------------------------------------------------------------------------
# grab_banner
# ---------------------------------------------------------------------------

class TestGrabBanner:
    def test_udp_returns_error(self):
        fp = grab_banner("host", 53, protocol="udp")
        assert fp.error != ""
        assert fp.banner == ""

    def test_successful_banner_grab(self):
        mock_sock = MagicMock()
        mock_sock.recv.return_value = b"SSH-2.0-OpenSSH\r\n"
        mock_sock.__enter__ = lambda s: s
        mock_sock.__exit__ = MagicMock(return_value=False)
        with patch("portwatch.fingerprint.socket.create_connection", return_value=mock_sock):
            fp = grab_banner("10.0.0.1", 22)
        assert fp.banner == "SSH-2.0-OpenSSH"
        assert fp.error == ""

    def test_connection_error_captured(self):
        with patch("portwatch.fingerprint.socket.create_connection", side_effect=OSError("refused")):
            fp = grab_banner("10.0.0.1", 9999)
        assert "refused" in fp.error
        assert fp.banner == ""

    def test_fingerprint_ports_returns_list(self):
        with patch("portwatch.fingerprint.grab_banner") as mock_grab:
            mock_grab.side_effect = lambda h, p, **kw: Fingerprint(host=h, port=p, protocol="tcp")
            result = fingerprint_ports("host", [22, 80, 443])
        assert len(result) == 3
        assert {fp.port for fp in result} == {22, 80, 443}


# ---------------------------------------------------------------------------
# fingerprint_store
# ---------------------------------------------------------------------------

class TestFingerprintStore:
    def test_save_and_load_round_trip(self, tmp_path):
        fps = [
            Fingerprint(host="10.0.0.1", port=22, protocol="tcp", banner="SSH"),
            Fingerprint(host="10.0.0.1", port=80, protocol="tcp", banner="HTTP"),
        ]
        save_fingerprints(fps, data_dir=tmp_path)
        loaded = load_fingerprints("10.0.0.1", data_dir=tmp_path)
        assert loaded is not None
        assert len(loaded) == 2
        assert {fp.port for fp in loaded} == {22, 80}

    def test_load_missing_returns_none(self, tmp_path):
        assert load_fingerprints("192.168.1.1", data_dir=tmp_path) is None

    def test_diff_detects_changed_banner(self):
        prev = [Fingerprint(host="h", port=80, protocol="tcp", banner="v1")]
        curr = [Fingerprint(host="h", port=80, protocol="tcp", banner="v2")]
        diffs = diff_fingerprints(prev, curr)
        assert len(diffs) == 1
        old, new = diffs[0]
        assert old.banner == "v1"
        assert new.banner == "v2"

    def test_diff_ignores_unchanged(self):
        prev = [Fingerprint(host="h", port=22, protocol="tcp", banner="same")]
        curr = [Fingerprint(host="h", port=22, protocol="tcp", banner="same")]
        assert diff_fingerprints(prev, curr) == []

    def test_diff_ignores_new_ports(self):
        prev: list = []
        curr = [Fingerprint(host="h", port=443, protocol="tcp", banner="TLS")]
        assert diff_fingerprints(prev, curr) == []
