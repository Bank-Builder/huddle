"""Battery status collector via sysfs (no subprocess)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _iter_batteries(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.name.upper().startswith("BAT") and path.is_dir()
    )


def _read_value(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


class BatteryCollector(Collector):
    """Read primary battery capacity and status from sysfs."""

    name = "battery"
    interval = 60.0

    def __init__(
        self,
        *,
        power_supply_root: Path | None = None,
        list_batteries: Callable[[Path], Iterable[Path]] | None = None,
        read_text: Callable[[Path], str | None] | None = None,
    ) -> None:
        self._root = (
            power_supply_root
            if power_supply_root is not None
            else Path("/sys/class/power_supply")
        )
        self._list = list_batteries if list_batteries is not None else _iter_batteries
        self._read = read_text if read_text is not None else _read_value

    def collect(self) -> dict[str, Any]:
        batteries = list(self._list(self._root))
        if not batteries:
            return {
                "present": False,
                "percent": None,
                "status": None,
                "name": None,
            }
        bat = batteries[0]
        capacity_raw = self._read(bat / "capacity")
        status = self._read(bat / "status")
        percent: int | None = None
        if capacity_raw is not None and capacity_raw.isdigit():
            percent = int(capacity_raw)
        return {
            "present": True,
            "percent": percent,
            "status": status,
            "name": bat.name,
        }
