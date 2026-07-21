"""Built-in and plugin collector package."""

from hudctl.collectors.base import Collector
from hudctl.collectors.clock import ClockCollector
from hudctl.collectors.cpu import CpuCollector
from hudctl.collectors.cwd import CwdCollector
from hudctl.collectors.git import GitCollector
from hudctl.collectors.memory import MemoryCollector
from hudctl.collectors.network import NetworkCollector

__all__ = [
    "ClockCollector",
    "Collector",
    "CpuCollector",
    "CwdCollector",
    "GitCollector",
    "MemoryCollector",
    "NetworkCollector",
]
