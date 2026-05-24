"""Tests for portwatch.plugin registry."""

from __future__ import annotations

import pytest

from portwatch.plugin import (
    Plugin,
    PluginMeta,
    dispatch,
    get_plugin,
    list_plugins,
    register_plugin,
    reset_registry,
    unregister_plugin,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    reset_registry()
    yield
    reset_registry()


def _make_plugin(name: str = "test") -> Plugin:
    return Plugin(meta=PluginMeta(name=name, description="test plugin"))


class TestPluginMeta:
    def test_as_dict_structure(self):
        meta = PluginMeta(name="demo", version="2.0", description="d", author="a")
        d = meta.as_dict()
        assert d["name"] == "demo"
        assert d["version"] == "2.0"
        assert d["description"] == "d"
        assert d["author"] == "a"

    def test_defaults(self):
        meta = PluginMeta(name="x")
        assert meta.version == "0.1.0"
        assert meta.description == ""
        assert meta.author == ""


class TestRegisterPlugin:
    def test_register_and_retrieve(self):
        p = _make_plugin("alpha")
        register_plugin(p)
        assert get_plugin("alpha") is p

    def test_duplicate_raises(self):
        register_plugin(_make_plugin("dup"))
        with pytest.raises(ValueError, match="already registered"):
            register_plugin(_make_plugin("dup"))

    def test_list_plugins_returns_metas(self):
        register_plugin(_make_plugin("a"))
        register_plugin(_make_plugin("b"))
        names = [m.name for m in list_plugins()]
        assert "a" in names and "b" in names

    def test_unregister_returns_true_when_existed(self):
        register_plugin(_make_plugin("rem"))
        assert unregister_plugin("rem") is True
        assert get_plugin("rem") is None

    def test_unregister_returns_false_when_missing(self):
        assert unregister_plugin("ghost") is False


class TestDispatch:
    def test_dispatch_calls_matching_handler(self):
        calls = []
        p = Plugin(
            meta=PluginMeta(name="spy"),
            on_scan_start=lambda **kw: calls.append(kw),
        )
        register_plugin(p)
        count = dispatch("on_scan_start", host="localhost", ports=[80])
        assert count == 1
        assert calls[0]["host"] == "localhost"

    def test_dispatch_skips_none_handler(self):
        register_plugin(_make_plugin("noop"))
        count = dispatch("on_scan_start", host="h", ports=[])
        assert count == 0

    def test_dispatch_returns_invoked_count(self):
        for name in ("p1", "p2", "p3"):
            p = Plugin(meta=PluginMeta(name=name), on_error=lambda **kw: None)
            register_plugin(p)
        assert dispatch("on_error", host="h", error=Exception()) == 3
