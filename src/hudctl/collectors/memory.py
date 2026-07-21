"""Memory usage collector via /proc/meminfo (no subprocesses)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_meminfo(text: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        parts = raw.split()
        if not parts:
            continue
        values[key] = int(parts[0])
    return values


class MemoryCollector(Collector):
    """Collect memory pressure from /proc/meminfo without subprocesses."""

    name = "memory"
    interval = 2.0

    def __init__(
        self,
        *,
        meminfo_path: Path | None = None,
        read_text: Callable[[Path], str] | None = None,
    ) -> None:
        self._meminfo_path = (
            meminfo_path if meminfo_path is not None else Path("/proc/meminfo")
        )
        self._read_text = read_text if read_text is not None else _read_text

    def collect(self) -> dict[str, Any]:
        info = _parse_meminfo(self._read_text(self._meminfo_path))
        total = info.get("MemTotal", 0)
        available = info.get("MemAvailable", info.get("MemFree", 0))
        used = max(0, total - available)
        percent = round((used / total) * 100.0, 1) if total else 0.0
        return {
            "total_kb": total,
            "available_kb": available,
            "used_kb": used,
            "percent": percent,
        }
