"""Hostname collector."""

from __future__ import annotations

import socket
from collections.abc import Callable
from typing import Any

from hudctl.collectors.base import Collector


class HostnameCollector(Collector):
    """Collect the system hostname (stdlib only, no subprocess)."""

    name = "hostname"
    interval = 60.0

    def __init__(self, *, gethostname: Callable[[], str] | None = None) -> None:
        self._gethostname = gethostname if gethostname is not None else socket.gethostname

    def collect(self) -> dict[str, Any]:
        full = self._gethostname()
        short = full.split(".", 1)[0]
        return {
            "hostname": full,
            "short": short,
        }
