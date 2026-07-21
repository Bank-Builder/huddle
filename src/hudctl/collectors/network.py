"""Network throughput collector via /proc/net/dev (no subprocesses)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_net_dev(text: str) -> tuple[int, int]:
    """Return aggregate (rx_bytes, tx_bytes) excluding loopback."""
    rx_total = 0
    tx_total = 0
    for line in text.splitlines()[2:]:
        if ":" not in line:
            continue
        iface, rest = line.split(":", 1)
        name = iface.strip()
        if name == "lo":
            continue
        parts = rest.split()
        if len(parts) < 9:
            continue
        rx_total += int(parts[0])
        tx_total += int(parts[8])
    return rx_total, tx_total


class NetworkCollector(Collector):
    """Collect aggregate NIC throughput from /proc/net/dev deltas.

    No subprocesses. First sample seeds counters; later samples yield rates.
    """

    name = "network"
    interval = 1.0

    def __init__(
        self,
        *,
        net_dev_path: Path | None = None,
        read_text: Callable[[Path], str] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._net_dev_path = (
            net_dev_path if net_dev_path is not None else Path("/proc/net/dev")
        )
        self._read_text = read_text if read_text is not None else _read_text
        if monotonic is None:
            from time import monotonic as _monotonic

            self._monotonic = _monotonic
        else:
            self._monotonic = monotonic
        self._prev_rx: int | None = None
        self._prev_tx: int | None = None
        self._prev_ts: float | None = None

    def collect(self) -> dict[str, Any]:
        rx, tx = _parse_net_dev(self._read_text(self._net_dev_path))
        now = self._monotonic()
        rx_bps: float | None = None
        tx_bps: float | None = None
        if (
            self._prev_rx is not None
            and self._prev_tx is not None
            and self._prev_ts is not None
        ):
            elapsed = now - self._prev_ts
            if elapsed > 0:
                rx_bps = max(0.0, (rx - self._prev_rx) / elapsed)
                tx_bps = max(0.0, (tx - self._prev_tx) / elapsed)
        self._prev_rx = rx
        self._prev_tx = tx
        self._prev_ts = now
        return {
            "rx_bytes": rx,
            "tx_bytes": tx,
            "rx_bps": None if rx_bps is None else round(rx_bps, 1),
            "tx_bps": None if tx_bps is None else round(tx_bps, 1),
        }
