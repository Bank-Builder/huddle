"""Tests for BatteryCollector and VpnCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.battery import BatteryCollector
from hudctl.collectors.vpn import VpnCollector


def test_battery_absent(tmp_path: Path) -> None:
    root = tmp_path / "power_supply"
    root.mkdir()
    data = BatteryCollector(power_supply_root=root).collect()
    assert data["present"] is False
    assert data["percent"] is None


def test_battery_reads_capacity(tmp_path: Path) -> None:
    bat = tmp_path / "power_supply" / "BAT0"
    bat.mkdir(parents=True)
    (bat / "capacity").write_text("87\n", encoding="utf-8")
    (bat / "status").write_text("Discharging\n", encoding="utf-8")
    data = BatteryCollector(power_supply_root=tmp_path / "power_supply").collect()
    assert data["present"] is True
    assert data["percent"] == 87
    assert data["status"] == "Discharging"
    assert data["name"] == "BAT0"


def test_vpn_detects_wg_and_tun(tmp_path: Path) -> None:
    net = tmp_path / "net"
    for name in ("lo", "eth0", "wg0", "tun0"):
        (net / name).mkdir(parents=True)
    data = VpnCollector(net_root=net).collect()
    assert data["active"] is True
    assert data["interfaces"] == ["tun0", "wg0"]
    assert data["primary"] == "tun0"


def test_vpn_inactive(tmp_path: Path) -> None:
    net = tmp_path / "net"
    (net / "eth0").mkdir(parents=True)
    data = VpnCollector(net_root=net).collect()
    assert data["active"] is False
    assert data["interfaces"] == []
