"""Hooks that attach tag metadata to scan reports and alert payloads."""

from __future__ import annotations

from typing import Any, Dict, List

from portwatch.tag import TagRegistry
from portwatch.scanner import PortState
from portwatch.alerts import PortChange

_registry: TagRegistry = TagRegistry()


def get_registry() -> TagRegistry:
    """Return the global TagRegistry instance."""
    return _registry


def reset_registry() -> None:
    """Replace the global registry with a fresh instance (useful in tests)."""
    global _registry
    _registry = TagRegistry()


def annotate_state(state: PortState) -> Dict[str, Any]:
    """Return a dict with tag names attached to a PortState."""
    reg = get_registry()
    host_tags = [t.name for t in reg.tags_for_host(state.host)]
    port_tags = [t.name for t in reg.tags_for_port(state.host, state.port)]
    return {
        "host": state.host,
        "port": state.port,
        "status": state.status,
        "tags": sorted(set(host_tags + port_tags)),
    }


def annotate_change(change: PortChange) -> Dict[str, Any]:
    """Return a dict with tag names attached to a PortChange."""
    reg = get_registry()
    host_tags = [t.name for t in reg.tags_for_host(change.host)]
    port_tags = [t.name for t in reg.tags_for_port(change.host, change.port)]
    return {
        "host": change.host,
        "port": change.port,
        "change": change.kind,
        "tags": sorted(set(host_tags + port_tags)),
    }


def annotate_changes(changes: List[PortChange]) -> List[Dict[str, Any]]:
    """Annotate a list of PortChange objects with tag metadata."""
    return [annotate_change(c) for c in changes]


def tags_for_change(change: PortChange) -> List[str]:
    """Return a flat list of tag names relevant to a PortChange."""
    annotated = annotate_change(change)
    return annotated["tags"]
