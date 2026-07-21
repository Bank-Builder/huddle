"""Tests for the context engine."""

from __future__ import annotations

from typing import Any

import pytest

from hudctl.collectors.base import Collector
from hudctl.engine import Engine
from hudctl.events import EventBus, SectionUpdated


class CountingCollector(Collector):
    name = "count"
    interval = 1.0

    def __init__(self) -> None:
        self.calls = 0

    def collect(self) -> dict[str, Any]:
        self.calls += 1
        return {"calls": self.calls}


class BoomCollector(Collector):
    name = "boom"
    interval = 1.0

    def collect(self) -> dict[str, Any]:
        msg = "boom"
        raise RuntimeError(msg)


class BadReturnCollector(Collector):
    name = "bad"
    interval = 1.0

    def collect(self) -> dict[str, Any]:
        return "nope"  # type: ignore[return-value]


def test_register_and_collect_updates_state_and_events() -> None:
    bus = EventBus()
    seen: list[SectionUpdated] = []
    bus.subscribe_all(seen.append)
    engine = Engine(bus)
    collector = CountingCollector()
    engine.register(collector)

    assert engine.collect_once("count") is True
    assert engine.state.get("count") == {"calls": 1}
    assert seen[0].section == "count"
    assert collector.calls == 1


def test_collect_all_isolates_failures() -> None:
    engine = Engine()
    engine.register(CountingCollector())
    engine.register(BoomCollector())
    results = engine.collect_all()
    assert results == {"count": True, "boom": False}
    assert engine.state.get("count") == {"calls": 1}
    assert engine.state.get("boom") is None


def test_bad_return_type_is_isolated() -> None:
    engine = Engine()
    engine.register(BadReturnCollector())
    assert engine.collect_once("bad") is False
    assert engine.state.get("bad") is None


def test_duplicate_and_invalid_registration() -> None:
    engine = Engine()
    engine.register(CountingCollector())
    with pytest.raises(ValueError, match="already registered"):
        engine.register(CountingCollector())

    class ZeroInterval(Collector):
        name = "zero"
        interval = 0

        def collect(self) -> dict[str, Any]:
            return {}

    with pytest.raises(ValueError, match="positive"):
        engine.register(ZeroInterval())


def test_unknown_collector_raises() -> None:
    engine = Engine()
    with pytest.raises(KeyError, match="unknown"):
        engine.collect_once("missing")
