"""Current working directory collector."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


class CwdCollector(Collector):
    """Resolve the process working directory, expanding symlinks when possible."""

    name = "cwd"
    interval = 2.0

    def __init__(
        self,
        *,
        getcwd: Callable[[], str] | None = None,
        home: Callable[[], Path] | None = None,
    ) -> None:
        self._getcwd = getcwd if getcwd is not None else os.getcwd
        self._home = home if home is not None else Path.home

    def collect(self) -> dict[str, Any]:
        raw = Path(self._getcwd())
        try:
            resolved = raw.resolve(strict=False)
        except OSError:
            resolved = raw

        home = self._home()
        display = str(resolved)
        try:
            display = f"~/{resolved.relative_to(home)}"
        except ValueError:
            display = str(resolved)

        return {
            "path": str(resolved),
            "logical": str(raw),
            "display": display,
            "basename": resolved.name or str(resolved),
        }
