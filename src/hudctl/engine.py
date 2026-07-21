"""Context engine: register collectors, update state, emit events."""

from __future__ import annotations

import logging
from typing import Any, cast

from hudctl.collectors.base import Collector
from hudctl.events import EventBus, SectionUpdated
from hudctl.state import ContextState

logger = logging.getLogger(__name__)


class Engine:
    """Own context state and apply collector updates safely."""

    def __init__(self, bus: EventBus | None = None) -> None:
        self._bus = bus if bus is not None else EventBus()
        self._state = ContextState()
        self._collectors: dict[str, Collector] = {}

    @property
    def bus(self) -> EventBus:
        """Return the event bus used for section updates."""
        return self._bus

    @property
    def state(self) -> ContextState:
        """Return the current immutable context state."""
        return self._state

    def register(self, collector: Collector) -> None:
        """Register a collector; names must be unique."""
        if collector.name in self._collectors:
            msg = f"collector already registered: {collector.name}"
            raise ValueError(msg)
        if collector.interval <= 0:
            msg = f"collector interval must be positive: {collector.name}"
            raise ValueError(msg)
        self._collectors[collector.name] = collector

    def collectors(self) -> tuple[Collector, ...]:
        """Return registered collectors in registration order."""
        return tuple(self._collectors.values())

    def collect_once(self, name: str) -> bool:
        """Run one collector by name.

        Returns True on success. Failures are logged and isolated; state is
        left unchanged for that section.
        """
        collector = self._collectors.get(name)
        if collector is None:
            msg = f"unknown collector: {name}"
            raise KeyError(msg)
        return self._run_collector(collector)

    def collect_all(self) -> dict[str, bool]:
        """Run every registered collector once; isolate failures per name."""
        return {
            name: self._run_collector(col) for name, col in self._collectors.items()
        }

    def snapshot(self) -> dict[str, dict[str, Any]]:
        """Return a deep copy of the current state sections."""
        return self._state.snapshot()

    def _run_collector(self, collector: Collector) -> bool:
        try:
            # Collectors are typed to return dict; validate at runtime for plugins.
            data = cast(Any, collector.collect())
        except Exception:
            logger.exception("collector failed: %s", collector.name)
            return False
        if not isinstance(data, dict):
            logger.error(
                "collector %s returned %s, expected dict",
                collector.name,
                type(data).__name__,
            )
            return False
        typed: dict[str, Any] = dict(data)
        self._state = self._state.with_section(collector.name, typed)
        self._bus.emit(SectionUpdated(collector.name, typed))
        return True
