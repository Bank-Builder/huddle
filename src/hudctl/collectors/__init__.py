"""Built-in and plugin collector package."""

from hudctl.collectors.base import Collector
from hudctl.collectors.battery import BatteryCollector
from hudctl.collectors.clock import ClockCollector
from hudctl.collectors.cpu import CpuCollector
from hudctl.collectors.cwd import CwdCollector
from hudctl.collectors.docker import DockerCollector
from hudctl.collectors.git import GitCollector
from hudctl.collectors.hostname import HostnameCollector
from hudctl.collectors.kubernetes import KubernetesCollector
from hudctl.collectors.memory import MemoryCollector
from hudctl.collectors.network import NetworkCollector
from hudctl.collectors.ssh import SshCollector
from hudctl.collectors.vpn import VpnCollector

__all__ = [
    "BatteryCollector",
    "ClockCollector",
    "Collector",
    "CpuCollector",
    "CwdCollector",
    "DockerCollector",
    "GitCollector",
    "HostnameCollector",
    "KubernetesCollector",
    "MemoryCollector",
    "NetworkCollector",
    "SshCollector",
    "VpnCollector",
]
