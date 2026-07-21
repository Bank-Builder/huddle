"""Renderer interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from hudctl.theme import Theme


class Renderer(ABC):
    """Transform context state into a consumer-specific string.

    Renderers are pure: they never collect system data or run shell commands.
    """

    name: str

    @abstractmethod
    def render(
        self,
        state: Mapping[str, Mapping[str, Any]],
        theme: Theme,
    ) -> str:
        """Return rendered output for ``state``."""
