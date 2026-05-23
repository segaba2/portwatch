"""Tests for portwatch.config (including suppression integration)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from portwatch.config import load_config, load_config_or_default, Config
from portwatch.suppression import SuppressionList


@pytest.fixture()
def full_config_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        hosts = ["192.168.1.1", "10.0.0.1"]
        ports = [22, 80, "8000-8002", 443]
        timeout = 2.5
        interval = 120
        state_dir = "/tmp/portwatch"

        [notify]
        webhook_url = "https://hooks.example.com/abc"
        email_to = "ops@example.com"
        email_from = "portwatch@example.com"
        smtp_host = "mail.example.com"
        smtp_port = 587

        [[suppression]]
        host = "192.168.1.1"
        port = 22
        protocol = "tcp"

        [[suppression]]
        host = "*"
        port = 80
        protocol = "*"
    """)
    p = tmp_path / "portwatch.toml"
    p.write_text(content)
    return p


class TestLoadConfig:
    def test_hosts(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.hosts == ["192.168.1.1", "10.0.0.1"]

    def test_ports_and_range(self, full_config_file):
        cfg = load_config(full_config_file)
        assert 22 in cfg.ports
        assert 8000 in cfg.ports
        assert 8001 in cfg.ports
        assert 8002 in cfg.ports
        assert 443 in cfg.ports

    def test_timeout(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.timeout == 2.5

    def test_interval(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.interval == 120

    def test_state_dir(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.state_dir == Path("/tmp/portwatch")

    def test_webhook_url(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.webhook_url == "https://hooks.example.com/abc"

    def test_smtp_port(self, full_config_file):
        cfg = load_config(full_config_file)
        assert cfg.smtp_port == 587

    def test_suppression_rules_loaded(self, full_config_file):
        cfg = load_config(full_config_file)
        assert isinstance(cfg.suppression, SuppressionList)
        assert len(cfg.suppression.rules) == 2

    def test_suppression_exact_rule(self, full_config_file):
        cfg = load_config(full_config_file)
        rule = cfg.suppression.rules[0]
        assert rule.host == "192.168.1.1"
        assert rule.port == 22
        assert rule.protocol == "tcp"

    def test_suppression_wildcard_rule(self, full_config_file):
        cfg = load_config(full_config_file)
        rule = cfg.suppression.rules[1]
        assert rule.host == "*"
        assert rule.protocol == "*"

    def test_effective_ports_sorted_unique(self, full_config_file):
        cfg = load_config(full_config_file)
        ep = cfg.effective_ports()
        assert ep == sorted(set(ep))


class TestLoadConfigOrDefault:
    def test_returns_default_when_missing(self, tmp_path):
        cfg = load_config_or_default(tmp_path / "missing.toml")
        assert isinstance(cfg, Config)
        assert cfg.hosts == []
        assert isinstance(cfg.suppression, SuppressionList)

    def test_loads_file_when_present(self, full_config_file):
        cfg = load_config_or_default(full_config_file)
        assert cfg.hosts != []
