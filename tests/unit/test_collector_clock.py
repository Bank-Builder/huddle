"""Tests for ClockCollector."""

from __future__ import annotations

from datetime import UTC, datetime

from hudctl.collectors.clock import ClockCollector


def test_clock_collector_returns_structured_time() -> None:
    fixed = datetime(2026, 7, 21, 16, 41, 0, tzinfo=UTC)

    def now() -> datetime:
        return fixed

    data = ClockCollector(now=now).collect()
    assert data["iso_utc"].startswith("2026-07-21T16:41:00")
    assert data["hhmm"]
    assert isinstance(data["epoch"], float)
