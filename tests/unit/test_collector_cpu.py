"""Tests for CpuCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.cpu import CpuCollector


def test_cpu_collector_computes_delta_percent(tmp_path: Path) -> None:
    samples = [
        "cpu  100 0 0 100 0 0 0 0 0 0\n",
        "cpu  150 0 0 110 0 0 0 0 0 0\n",
    ]

    def read_text(_path: Path) -> str:
        return samples.pop(0)

    collector = CpuCollector(stat_path=tmp_path / "stat", read_text=read_text)
    first = collector.collect()
    second = collector.collect()
    assert first["percent"] is None
    # idle delta 10, total delta 60 => ~83.3% busy
    assert second["percent"] == 83.3
