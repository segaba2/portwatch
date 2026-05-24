"""Plugin registry for portwatch — allows third-party extensions to hook into scan lifecycle events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class PluginMeta:
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
        }


@dataclass
class Plugin:
    meta: PluginMeta
    on_scan_start: Optional[Callable] = None
    on_scan_complete: Optional[Callable] = None
    on_changes_detected: Optional[Callable] = None
    on_alert_sent: Optional[Callable] = None
    on_error: Optional[Callable] = None


_registry: Dict[str, Plugin] = {}


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin by its name. Raises ValueError on duplicate."""
    name = plugin.meta.name
    if name in _registry:
        raise ValueError(f"Plugin '{name}' is already registered.")
    _registry[name] = plugin


def unregister_plugin(name: str) -> bool:
    """Remove a plugin by name. Returns True if it existed."""
    return _registry.pop(name, None) is not None


def get_plugin(name: str) -> Optional[Plugin]:
    return _registry.get(name)


def list_plugins() -> List[PluginMeta]:
    return [p.meta for p in _registry.values()]


def reset_registry() -> None:
    """Clear all registered plugins (primarily for testing)."""
    _registry.clear()


def dispatch(event: str, *args, **kwargs) -> int:
    """Call the named hook on every registered plugin. Returns count of plugins invoked."""
    count = 0
    for plugin in _registry.values():
        handler = getattr(plugin, event, None)
        if callable(handler):
            handler(*args, **kwargs)
            count += 1
    return count
