"""Tests for the asyncio collector scheduler."""

from __future__ import annotations

import asyncio
from typing import Any

from hudctl.collectors.base import Collector
from hudctl.engine import Engine
from hudctl.scheduler import Scheduler


class TickCollector(Collector):
    def __init__(self, name: str, interval: float) -> None:
        self.name = name
        self.interval = interval
        self.calls = 0

    def collect(self) -> dict[str, Any]:
        self.calls += 1
        return {"calls": self.calls}


class FailThenOkCollector(Collector):
    name = "flaky"
    interval = 0.01

    def __init__(self) -> None:
        self.calls = 0

    def collect(self) -> dict[str, Any]:
        self.calls += 1
        if self.calls == 1:
            msg = "first call fails"
            raise RuntimeError(msg)
        return {"calls": self.calls}


def test_scheduler_runs_collectors_independently() -> None:
    async def _run() -> None:
        engine = Engine()
        fast = TickCollector("fast", 0.01)
        slow = TickCollector("slow", 0.05)
        engine.register(fast)
        engine.register(slow)
        scheduler = Scheduler(engine)
        stop = asyncio.Event()

        async def stop_soon() -> None:
            await asyncio.sleep(0.06)
            stop.set()

        await asyncio.gather(scheduler.run(stop), stop_soon())
        assert fast.calls >= 2
        assert slow.calls >= 1
        assert engine.state.get("fast") is not None
        assert engine.state.get("slow") is not None

    asyncio.run(_run())


def test_scheduler_isolates_collector_errors() -> None:
    async def _run() -> None:
        engine = Engine()
        flaky = FailThenOkCollector()
        other = TickCollector("other", 0.01)
        engine.register(flaky)
        engine.register(other)
        scheduler = Scheduler(engine)
        stop = asyncio.Event()

        async def stop_soon() -> None:
            await asyncio.sleep(0.05)
            stop.set()

        await asyncio.gather(scheduler.run(stop), stop_soon())
        assert flaky.calls >= 2
        assert other.calls >= 1
        assert engine.state.get("flaky") == {"calls": flaky.calls}
        assert engine.state.get("other") is not None

    asyncio.run(_run())


def test_scheduler_with_no_collectors_waits_for_stop() -> None:
    async def _run() -> None:
        scheduler = Scheduler(Engine())
        stop = asyncio.Event()

        async def stop_soon() -> None:
            await asyncio.sleep(0.01)
            stop.set()

        await asyncio.gather(scheduler.run(stop), stop_soon())

    asyncio.run(_run())
