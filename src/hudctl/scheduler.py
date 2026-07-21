"""Asyncio scheduler that runs collectors on independent intervals."""

from __future__ import annotations

import asyncio
import logging

from hudctl.engine import Engine

logger = logging.getLogger(__name__)


class Scheduler:
    """Run each collector loop independently without blocking siblings."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    async def run(self, stop_event: asyncio.Event) -> None:
        """Run collector tasks until ``stop_event`` is set."""
        collectors = self._engine.collectors()
        if not collectors:
            await stop_event.wait()
            return

        tasks = [
            asyncio.create_task(
                self._run_collector_loop(
                    collector.name,
                    collector.interval,
                    stop_event,
                ),
                name=f"hudctl-collector-{collector.name}",
            )
            for collector in collectors
        ]
        try:
            await stop_event.wait()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_collector_loop(
        self,
        name: str,
        interval: float,
        stop_event: asyncio.Event,
    ) -> None:
        while not stop_event.is_set():
            self._engine.collect_once(name)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                return
            except TimeoutError:
                continue
