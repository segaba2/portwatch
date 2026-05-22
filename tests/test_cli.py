"""Tests for the portwatch CLI."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from portwatch.cli import build_parser, main


class TestBuildParser:
    def test_default_config_path(self):
        parser = build_parser()
        args = parser.parse_args(["scan"])
        assert args.config == Path("portwatch/portwatch.toml")

    def test_custom_config_path(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "/tmp/my.toml", "scan"])
        assert args.config == Path("/tmp/my.toml")

    def test_scan_command_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["scan"])
        assert args.command == "scan"
        assert args.no_notify is False

    def test_scan_no_notify_flag(self):
        parser = build_parser()
        args = parser.parse_args(["scan", "--no-notify"])
        assert args.no_notify is True

    def test_daemon_command_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["daemon"])
        assert args.command == "daemon"
        assert args.interval is None

    def test_daemon_interval_override(self):
        parser = build_parser()
        args = parser.parse_args(["daemon", "--interval", "120"])
        assert args.interval == 120

    def test_no_command_returns_zero(self):
        result = main([])
        assert result == 0


class TestMainScan:
    @patch("portwatch.cli.run_once")
    @patch("portwatch.cli.load_config_or_default")
    def test_scan_calls_run_once_with_notify(self, mock_load, mock_run_once):
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        result = main(["scan"])

        mock_run_once.assert_called_once_with(mock_config, notify=True)
        assert result == 0

    @patch("portwatch.cli.run_once")
    @patch("portwatch.cli.load_config_or_default")
    def test_scan_no_notify_passes_false(self, mock_load, mock_run_once):
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        result = main(["scan", "--no-notify"])

        mock_run_once.assert_called_once_with(mock_config, notify=False)
        assert result == 0


class TestMainDaemon:
    @patch("portwatch.cli.run_daemon")
    @patch("portwatch.cli.load_config_or_default")
    def test_daemon_calls_run_daemon(self, mock_load, mock_run_daemon):
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        result = main(["daemon"])

        mock_run_daemon.assert_called_once_with(mock_config)
        assert result == 0

    @patch("portwatch.cli.run_daemon")
    @patch("portwatch.cli.load_config_or_default")
    def test_daemon_interval_override_replaces_config(self, mock_load, mock_run_daemon):
        mock_config = MagicMock()
        mock_config._replace.return_value = mock_config
        mock_load.return_value = mock_config

        main(["daemon", "--interval", "60"])

        mock_config._replace.assert_called_once_with(interval=60)
        mock_run_daemon.assert_called_once_with(mock_config)
