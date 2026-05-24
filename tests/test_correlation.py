"""Tests for portwatch.correlation."""

from portwatch.alerts import PortChange
from portwatch.correlation import (
    CorrelationGroup,
    CorrelationResult,
    correlate_changes,
)


def _change(host: str, port: int, change_type: str = "opened") -> PortChange:
    return PortChange(host=host, port=port, change_type=change_type, protocol="tcp")


# ---------------------------------------------------------------------------
# CorrelationGroup
# ---------------------------------------------------------------------------

class TestCorrelationGroup:
    def test_is_widespread_single_host(self):
        g = CorrelationGroup(port=80, change_type="opened", hosts=["h1"])
        assert not g.is_widespread

    def test_is_widespread_multiple_hosts(self):
        g = CorrelationGroup(port=80, change_type="opened", hosts=["h1", "h2"])
        assert g.is_widespread

    def test_as_dict_structure(self):
        g = CorrelationGroup(port=443, change_type="closed", hosts=["a", "b", "c"])
        d = g.as_dict()
        assert d["port"] == 443
        assert d["change_type"] == "closed"
        assert d["host_count"] == 3
        assert set(d["hosts"]) == {"a", "b", "c"}


# ---------------------------------------------------------------------------
# CorrelationResult
# ---------------------------------------------------------------------------

class TestCorrelationResult:
    def test_widespread_groups_filters_correctly(self):
        g1 = CorrelationGroup(port=22, change_type="opened", hosts=["h1"])
        g2 = CorrelationGroup(port=80, change_type="opened", hosts=["h1", "h2"])
        result = CorrelationResult(groups=[g1, g2])
        assert result.widespread_groups == [g2]

    def test_has_widespread_false_when_all_single(self):
        g = CorrelationGroup(port=22, change_type="opened", hosts=["h1"])
        result = CorrelationResult(groups=[g])
        assert not result.has_widespread

    def test_as_dict_includes_widespread_count(self):
        g = CorrelationGroup(port=80, change_type="opened", hosts=["h1", "h2"])
        result = CorrelationResult(groups=[g])
        d = result.as_dict()
        assert d["widespread_count"] == 1


# ---------------------------------------------------------------------------
# correlate_changes
# ---------------------------------------------------------------------------

class TestCorrelateChanges:
    def test_empty_input(self):
        result = correlate_changes([])
        assert result.groups == []
        assert not result.has_widespread

    def test_single_change(self):
        result = correlate_changes([_change("host1", 80)])
        assert len(result.groups) == 1
        assert result.groups[0].port == 80
        assert result.groups[0].hosts == ["host1"]

    def test_same_port_different_hosts_grouped(self):
        changes = [
            _change("host1", 443),
            _change("host2", 443),
        ]
        result = correlate_changes(changes)
        assert len(result.groups) == 1
        g = result.groups[0]
        assert g.port == 443
        assert set(g.hosts) == {"host1", "host2"}
        assert g.is_widespread

    def test_different_ports_separate_groups(self):
        changes = [
            _change("host1", 22),
            _change("host1", 80),
        ]
        result = correlate_changes(changes)
        assert len(result.groups) == 2

    def test_same_host_not_duplicated_in_group(self):
        changes = [
            _change("host1", 8080),
            _change("host1", 8080),
        ]
        result = correlate_changes(changes)
        assert len(result.groups) == 1
        assert result.groups[0].hosts == ["host1"]

    def test_open_and_closed_are_separate_groups(self):
        changes = [
            _change("host1", 22, "opened"),
            _change("host2", 22, "closed"),
        ]
        result = correlate_changes(changes)
        assert len(result.groups) == 2
        types = {g.change_type for g in result.groups}
        assert types == {"opened", "closed"}
