"""Simple publish/subscribe event bus for section updates."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Listener = Callable[["SectionUpdated"], None]


@dataclass(frozen=True, slots=True)
class SectionUpdated:
    """Event emitted when a collector section changes."""

    section: str
    data: dict[str, Any]


class EventBus:
    """In-process pub/sub for engine events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._any_listeners: list[Listener] = []

    def subscribe(self, section: str, listener: Listener) -> None:
        """Subscribe to updates for a single section name."""
        self._listeners[section].append(listener)

    def subscribe_all(self, listener: Listener) -> None:
        """Subscribe to updates for every section."""
        self._any_listeners.append(listener)

    def unsubscribe(self, section: str, listener: Listener) -> None:
        """Remove a section-specific listener if present."""
        listeners = self._listeners.get(section)
        if not listeners:
            return
        try:
            listeners.remove(listener)
        except ValueError:
            return
        if not listeners:
            del self._listeners[section]

    def unsubscribe_all(self, listener: Listener) -> None:
        """Remove a global listener if present."""
        try:
            self._any_listeners.remove(listener)
        except ValueError:
            return

    def emit(self, event: SectionUpdated) -> None:
        """Notify listeners for ``event.section`` and global listeners."""
        for listener in list(self._listeners.get(event.section, ())):
            listener(event)
        for listener in list(self._any_listeners):
            listener(event)

    def clear(self) -> None:
        """Remove all listeners."""
        self._listeners.clear()
        self._any_listeners.clear()
