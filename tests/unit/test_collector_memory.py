"""Tests for MemoryCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.memory import MemoryCollector


def test_memory_collector_parses_meminfo(tmp_path: Path) -> None:
    text = "\n".join(
        [
            "MemTotal:       1000 kB",
            "MemFree:         200 kB",
            "MemAvailable:    400 kB",
        ]
    )

    data = MemoryCollector(
        meminfo_path=tmp_path / "meminfo",
        read_text=lambda _path: text,
    ).collect()

    assert data["total_kb"] == 1000
    assert data["available_kb"] == 400
    assert data["used_kb"] == 600
    assert data["percent"] == 60.0
