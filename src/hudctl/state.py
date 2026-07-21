"""Immutable sectional context state for the huddle engine."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ContextState:
    """Immutable snapshot of all collector sections.

    Collectors update only their own section via :meth:`with_section`.
    Renderers must consume a snapshot and never mutate it.
    """

    sections: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get(self, name: str) -> dict[str, Any] | None:
        """Return a deep copy of a section, or None if missing."""
        section = self.sections.get(name)
        if section is None:
            return None
        return deepcopy(section)

    def with_section(self, name: str, data: dict[str, Any]) -> ContextState:
        """Return a new state with ``name`` replaced by a deep copy of ``data``."""
        updated = {key: deepcopy(value) for key, value in self.sections.items()}
        updated[name] = deepcopy(data)
        return ContextState(sections=updated)

    def without_section(self, name: str) -> ContextState:
        """Return a new state with ``name`` removed if present."""
        if name not in self.sections:
            return self
        updated = {
            key: deepcopy(value) for key, value in self.sections.items() if key != name
        }
        return ContextState(sections=updated)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a deep copy of all sections as a plain dict."""
        return deepcopy(self.sections)

    def names(self) -> frozenset[str]:
        """Return the set of section names."""
        return frozenset(self.sections)
