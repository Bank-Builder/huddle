"""Tests for NetworkCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.network import NetworkCollector


def test_network_collector_rates(tmp_path: Path) -> None:
    samples = [
        (
            "Inter-|   Receive                                                |  Transmit\n"
            " face |bytes    packets errs drop fifo frame compressed multicast|bytes\n"
            "    lo: 10 0 0 0 0 0 0 0 10 0 0 0 0 0 0\n"
            "  eth0: 100 0 0 0 0 0 0 0 200 0 0 0 0 0 0\n"
        ),
        (
            "Inter-|   Receive                                                |  Transmit\n"
            " face |bytes    packets errs drop fifo frame compressed multicast|bytes\n"
            "    lo: 10 0 0 0 0 0 0 0 10 0 0 0 0 0 0\n"
            "  eth0: 300 0 0 0 0 0 0 0 500 0 0 0 0 0 0\n"
        ),
    ]
    times = iter([1.0, 3.0])

    def read_text(_path: Path) -> str:
        return samples.pop(0)

    collector = NetworkCollector(
        net_dev_path=tmp_path / "dev",
        read_text=read_text,
        monotonic=lambda: next(times),
    )
    first = collector.collect()
    second = collector.collect()
    assert first["rx_bps"] is None
    assert second["rx_bytes"] == 300
    assert second["tx_bytes"] == 500
    assert second["rx_bps"] == 100.0
    assert second["tx_bps"] == 150.0
