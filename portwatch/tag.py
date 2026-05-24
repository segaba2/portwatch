"""Tag support for labelling ports and hosts with user-defined metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Tag:
    name: str
    color: Optional[str] = None
    description: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "color": self.color,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        return cls(
            name=data["name"],
            color=data.get("color"),
            description=data.get("description", ""),
        )

    def __str__(self) -> str:
        return self.name


@dataclass
class TagRegistry:
    """Maps (host, port) pairs and hosts to lists of tag names."""

    _host_tags: Dict[str, List[str]] = field(default_factory=dict)
    _port_tags: Dict[str, List[str]] = field(default_factory=dict)
    _tags: Dict[str, Tag] = field(default_factory=dict)

    def register(self, tag: Tag) -> None:
        self._tags[tag.name] = tag

    def tag_host(self, host: str, tag_name: str) -> None:
        self._host_tags.setdefault(host, []).append(tag_name)

    def tag_port(self, host: str, port: int, tag_name: str) -> None:
        key = f"{host}:{port}"
        self._port_tags.setdefault(key, []).append(tag_name)

    def tags_for_host(self, host: str) -> List[Tag]:
        names = self._host_tags.get(host, [])
        return [self._tags[n] for n in names if n in self._tags]

    def tags_for_port(self, host: str, port: int) -> List[Tag]:
        key = f"{host}:{port}"
        names = self._port_tags.get(key, [])
        return [self._tags[n] for n in names if n in self._tags]

    def all_tags(self) -> List[Tag]:
        return list(self._tags.values())

    def as_dict(self) -> dict:
        return {
            "tags": [t.as_dict() for t in self._tags.values()],
            "host_tags": dict(self._host_tags),
            "port_tags": dict(self._port_tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TagRegistry":
        registry = cls()
        for td in data.get("tags", []):
            registry.register(Tag.from_dict(td))
        registry._host_tags = {k: list(v) for k, v in data.get("host_tags", {}).items()}
        registry._port_tags = {k: list(v) for k, v in data.get("port_tags", {}).items()}
        return registry
