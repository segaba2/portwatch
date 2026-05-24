"""Tests for portwatch.tag."""

import pytest
from portwatch.tag import Tag, TagRegistry


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------

class TestTag:
    def test_str_returns_name(self):
        t = Tag(name="critical")
        assert str(t) == "critical"

    def test_defaults(self):
        t = Tag(name="web")
        assert t.color is None
        assert t.description == ""

    def test_as_dict_structure(self):
        t = Tag(name="db", color="red", description="database ports")
        d = t.as_dict()
        assert d["name"] == "db"
        assert d["color"] == "red"
        assert d["description"] == "database ports"

    def test_round_trip(self):
        t = Tag(name="internal", color="blue", description="internal services")
        assert Tag.from_dict(t.as_dict()) == t

    def test_from_dict_missing_optionals(self):
        t = Tag.from_dict({"name": "plain"})
        assert t.color is None
        assert t.description == ""


# ---------------------------------------------------------------------------
# TagRegistry
# ---------------------------------------------------------------------------

@pytest.fixture()
def registry():
    reg = TagRegistry()
    reg.register(Tag(name="web", color="green"))
    reg.register(Tag(name="db", color="red"))
    return reg


class TestTagRegistry:
    def test_all_tags(self, registry):
        names = {t.name for t in registry.all_tags()}
        assert names == {"web", "db"}

    def test_tag_host_and_retrieve(self, registry):
        registry.tag_host("example.com", "web")
        tags = registry.tags_for_host("example.com")
        assert len(tags) == 1
        assert tags[0].name == "web"

    def test_tag_port_and_retrieve(self, registry):
        registry.tag_port("example.com", 5432, "db")
        tags = registry.tags_for_port("example.com", 5432)
        assert len(tags) == 1
        assert tags[0].name == "db"

    def test_tags_for_unknown_host_returns_empty(self, registry):
        assert registry.tags_for_host("unknown.host") == []

    def test_tags_for_unknown_port_returns_empty(self, registry):
        assert registry.tags_for_port("example.com", 9999) == []

    def test_unregistered_tag_name_silently_skipped(self):
        reg = TagRegistry()
        reg._host_tags["h"] = ["ghost"]
        assert reg.tags_for_host("h") == []

    def test_multiple_tags_on_host(self, registry):
        registry.tag_host("example.com", "web")
        registry.tag_host("example.com", "db")
        tags = registry.tags_for_host("example.com")
        assert {t.name for t in tags} == {"web", "db"}

    def test_round_trip(self, registry):
        registry.tag_host("h1", "web")
        registry.tag_port("h1", 80, "web")
        restored = TagRegistry.from_dict(registry.as_dict())
        assert {t.name for t in restored.all_tags()} == {"web", "db"}
        assert restored.tags_for_host("h1")[0].name == "web"
        assert restored.tags_for_port("h1", 80)[0].name == "web"

    def test_as_dict_structure(self, registry):
        d = registry.as_dict()
        assert "tags" in d
        assert "host_tags" in d
        assert "port_tags" in d
