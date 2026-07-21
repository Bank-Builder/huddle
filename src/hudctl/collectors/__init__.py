"""Built-in and plugin collector package."""

from hudctl.collectors.base import Collector
from hudctl.collectors.clock import ClockCollector
from hudctl.collectors.cpu import CpuCollector
from hudctl.collectors.cwd import CwdCollector
from hudctl.collectors.memory import MemoryCollector

__all__ = [
    "ClockCollector",
    "Collector",
    "CpuCollector",
    "CwdCollector",
    "MemoryCollector",
]
