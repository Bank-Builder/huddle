"""CPU usage collector via /proc/stat (no subprocesses)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_cpu_times(stat_text: str) -> tuple[int, int]:
    """Return (idle_all, total) jiffies from the aggregate cpu line."""
    for line in stat_text.splitlines():
        if line.startswith("cpu "):
            parts = line.split()
            values = [int(part) for part in parts[1:]]
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            total = sum(values)
            return idle, total
    msg = "cpu line not found in /proc/stat"
    raise ValueError(msg)


class CpuCollector(Collector):
    """Sample aggregate CPU utilisation from /proc/stat deltas.

    Avoids subprocesses; keep interval >= 1s so deltas are meaningful.
    """

    name = "cpu"
    interval = 2.0

    def __init__(
        self,
        *,
        stat_path: Path | None = None,
        read_text: Callable[[Path], str] | None = None,
    ) -> None:
        self._stat_path = stat_path if stat_path is not None else Path("/proc/stat")
        self._read_text = read_text if read_text is not None else _read_text
        self._prev_idle: int | None = None
        self._prev_total: int | None = None

    def collect(self) -> dict[str, Any]:
        idle, total = _parse_cpu_times(self._read_text(self._stat_path))
        percent: float | None = None
        if self._prev_idle is not None and self._prev_total is not None:
            idle_delta = idle - self._prev_idle
            total_delta = total - self._prev_total
            if total_delta > 0:
                percent = max(0.0, min(100.0, (1.0 - idle_delta / total_delta) * 100.0))
        self._prev_idle = idle
        self._prev_total = total
        return {
            "percent": None if percent is None else round(percent, 1),
            "idle_jiffies": idle,
            "total_jiffies": total,
        }
