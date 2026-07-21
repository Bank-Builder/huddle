"""SSH session detection collector."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from typing import Any

from hudctl.collectors.base import Collector


class SshCollector(Collector):
    """Detect whether the session is over SSH via environment variables."""

    name = "ssh"
    interval = 30.0

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._environ: Mapping[str, str] = (
            environ if environ is not None else os.environ
        )

    def collect(self) -> dict[str, Any]:
        connection = self._environ.get("SSH_CONNECTION")
        client = self._environ.get("SSH_CLIENT")
        tty = self._environ.get("SSH_TTY")
        active = bool(connection or client or tty)
        client_ip: str | None = None
        if connection:
            client_ip = connection.split()[0]
        elif client:
            client_ip = client.split()[0]
        return {
            "active": active,
            "client_ip": client_ip,
            "tty": tty,
        }
