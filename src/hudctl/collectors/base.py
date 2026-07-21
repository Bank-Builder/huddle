"""Collector interface for huddle context modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Collector(ABC):
    """Gather one section of structured context data.

    Collectors must never print or format display strings. They return
    structured data only. Scheduling and caching are owned by the engine.
    """

    name: str
    interval: float

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Return structured data for this collector's state section."""
