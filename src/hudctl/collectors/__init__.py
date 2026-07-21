"""Built-in and plugin collector package."""

from hudctl.collectors.base import Collector
from hudctl.collectors.clock import ClockCollector
from hudctl.collectors.cwd import CwdCollector

__all__ = ["ClockCollector", "Collector", "CwdCollector"]
