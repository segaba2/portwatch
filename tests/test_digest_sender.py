"""Tests for portwatch.digest_sender."""

from unittest.mock import MagicMock, patch

import pytest

from portwatch.alerts import PortChange
from portwatch.digest import Digest, DigestConfig, DigestEntry
from portwatch.digest_sender import maybe_flush_and_send
from portwatch.notifier import NotifierConfig


def _change(port: int = 80) -> PortChange:
    return PortChange(host="h1", port=port, protocol="tcp", kind="opened")


def _ready_digest(window: int = 0) -> Digest:
    """Return a digest that is immediately ready."""
    d = Digest(config=DigestConfig(enabled=True, window=window))
    with patch("portwatch.digest.time.time", return_value=0.0):
        d.add(_change())
    return d


class TestMaybeFlushAndSend:
    def test_returns_false_when_digest_disabled(self):
        d = Digest(config=DigestConfig(enabled=False))
        d.add(_change())
        result = maybe_flush_and_send(d, NotifierConfig(), force=True)
        assert result is False

    def test_returns_false_when_not_ready_and_no_force(self):
        d = Digest(config=DigestConfig(enabled=True, window=9999))
        d.add(_change())
        result = maybe_flush_and_send(d, NotifierConfig())
        assert result is False

    def test_returns_false_when_no_entries(self):
        d = Digest(config=DigestConfig(enabled=True, window=0))
        result = maybe_flush_and_send(d, NotifierConfig(), force=True)
        assert result is False

    def test_sends_webhook_when_configured(self):
        d = _ready_digest()
        notifier = NotifierConfig(webhook_url="http://example.com/hook")
        with patch("portwatch.digest_sender.send_webhook") as mock_wh, \
             patch("portwatch.digest.time.time", return_value=9999.0):
            result = maybe_flush_and_send(d, notifier)
        assert result is True
        mock_wh.assert_called_once()
        _, kwargs = mock_wh.call_args
        assert "text" in kwargs["payload"]

    def test_sends_email_when_configured(self):
        d = _ready_digest()
        notifier = NotifierConfig(
            smtp_host="smtp.example.com",
            email_to="ops@example.com",
        )
        with patch("portwatch.digest_sender.send_email") as mock_em, \
             patch("portwatch.digest.time.time", return_value=9999.0):
            result = maybe_flush_and_send(d, notifier)
        assert result is True
        mock_em.assert_called_once()

    def test_force_flushes_before_window_elapsed(self):
        d = Digest(config=DigestConfig(enabled=True, window=9999))
        with patch("portwatch.digest.time.time", return_value=0.0):
            d.add(_change(port=443))
        notifier = NotifierConfig(webhook_url="http://hook")
        with patch("portwatch.digest_sender.send_webhook"):
            result = maybe_flush_and_send(d, notifier, force=True)
        assert result is True
        assert d.pending_count() == 0

    def test_returns_false_when_no_channel_configured(self):
        d = _ready_digest()
        with patch("portwatch.digest.time.time", return_value=9999.0):
            result = maybe_flush_and_send(d, NotifierConfig())
        assert result is False
