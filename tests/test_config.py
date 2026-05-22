"""Tests for portwatch.config."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from portwatch.config import Config, load_config, load_config_or_default


TOML_FULL = textwrap.dedent("""\
    [scan]
    hosts = ["10.0.0.1", "10.0.0.2"]
    ports = [22, 80, 443]
    port_range = [8000, 8005]
    timeout = 2.5

    [daemon]
    interval_seconds = 30
    state_file = "/tmp/portwatch_test.json"

    [notify]
    webhook_url = "https://hooks.example.com/abc"

    [notify.smtp]
    host = "smtp.example.com"
    port = 465
    user = "user@example.com"
    password = "secret"
    from = "alerts@example.com"
    to = ["ops@example.com"]
""")


@pytest.fixture()
def full_config_file(tmp_path: Path) -> Path:
    p = tmp_path / "portwatch.toml"
    p.write_text(TOML_FULL, encoding="utf-8")
    return p


class TestLoadConfig:
    def test_hosts(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.hosts == ["10.0.0.1", "10.0.0.2"]

    def test_ports_and_range(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        effective = cfg.effective_ports()
        assert 22 in effective
        assert 8003 in effective
        assert len(effective) == len(set(effective)), "no duplicates"

    def test_timeout(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.scan_timeout == pytest.approx(2.5)

    def test_interval(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.interval_seconds == 30

    def test_state_file(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.state_file == Path("/tmp/portwatch_test.json")

    def test_webhook(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.webhook_url == "https://hooks.example.com/abc"

    def test_smtp(self, full_config_file: Path) -> None:
        cfg = load_config(full_config_file)
        assert cfg.smtp_host == "smtp.example.com"
        assert cfg.smtp_port == 465
        assert cfg.email_to == ["ops@example.com"]


class TestDefaults:
    def test_default_config(self) -> None:
        cfg = Config()
        assert cfg.hosts == ["127.0.0.1"]
        assert cfg.interval_seconds == 60
        assert cfg.scan_timeout == pytest.approx(1.0)

    def test_effective_ports_empty(self) -> None:
        cfg = Config()
        assert cfg.effective_ports() == []

    def test_effective_ports_range_only(self) -> None:
        cfg = Config(port_range=(100, 103))
        assert cfg.effective_ports() == [100, 101, 102, 103]


class TestLoadConfigOrDefault:
    def test_returns_default_when_path_is_none(self) -> None:
        cfg = load_config_or_default(None)
        assert isinstance(cfg, Config)

    def test_returns_default_when_file_missing(self, tmp_path: Path) -> None:
        cfg = load_config_or_default(tmp_path / "nonexistent.toml")
        assert isinstance(cfg, Config)

    def test_loads_file_when_present(self, full_config_file: Path) -> None:
        cfg = load_config_or_default(full_config_file)
        assert cfg.webhook_url == "https://hooks.example.com/abc"
