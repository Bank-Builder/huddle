"""Local clock collector (no subprocesses)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from hudctl.collectors.base import Collector


class ClockCollector(Collector):
    """Collect local and UTC wall-clock time.

    Cheap and allocation-light; safe to run every second.
    """

    name = "clock"
    interval = 1.0

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now if now is not None else datetime.now

    def collect(self) -> dict[str, Any]:
        local = self._now().astimezone()
        utc = local.astimezone(UTC)
        return {
            "iso_local": local.isoformat(timespec="seconds"),
            "iso_utc": utc.isoformat(timespec="seconds"),
            "epoch": local.timestamp(),
            "hhmm": local.strftime("%H:%M"),
        }
