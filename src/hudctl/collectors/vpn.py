"""VPN interface detection via sysfs / proc (no subprocess)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector

_VPN_PREFIXES = ("tun", "tap", "wg", "vpn", "proton", "nordlynx", "utun")


def _iter_ifaces(net_root: Path) -> Iterable[str]:
    if not net_root.is_dir():
        return []
    return sorted(path.name for path in net_root.iterdir() if path.is_dir())


def _is_vpn_iface(name: str) -> bool:
    lower = name.lower()
    return any(lower == prefix or lower.startswith(prefix) for prefix in _VPN_PREFIXES)


class VpnCollector(Collector):
    """Detect likely VPN network interfaces from /sys/class/net."""

    name = "vpn"
    interval = 30.0

    def __init__(
        self,
        *,
        net_root: Path | None = None,
        list_ifaces: Callable[[Path], Iterable[str]] | None = None,
    ) -> None:
        self._net_root = net_root if net_root is not None else Path("/sys/class/net")
        self._list = list_ifaces if list_ifaces is not None else _iter_ifaces

    def collect(self) -> dict[str, Any]:
        ifaces = [name for name in self._list(self._net_root) if _is_vpn_iface(name)]
        return {
            "active": bool(ifaces),
            "interfaces": ifaces,
            "primary": ifaces[0] if ifaces else None,
        }
