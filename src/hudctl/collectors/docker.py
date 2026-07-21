"""Docker environment collector (filesystem probes, no subprocess)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _path_exists(path: Path) -> bool:
    return path.exists()


class DockerCollector(Collector):
    """Detect Docker socket availability and container membership.

    Avoids ``docker`` CLI invocations. Reports presence only.
    """

    name = "docker"
    interval = 30.0

    def __init__(
        self,
        *,
        socket_path: Path | None = None,
        dockerenv_path: Path | None = None,
        cgroup_path: Path | None = None,
        exists: Callable[[Path], bool] | None = None,
        read_text: Callable[[Path], str] | None = None,
    ) -> None:
        self._socket_path = (
            socket_path if socket_path is not None else Path("/var/run/docker.sock")
        )
        self._dockerenv_path = (
            dockerenv_path if dockerenv_path is not None else Path("/.dockerenv")
        )
        self._cgroup_path = (
            cgroup_path if cgroup_path is not None else Path("/proc/1/cgroup")
        )
        self._exists = exists if exists is not None else _path_exists
        self._read_text = (
            read_text
            if read_text is not None
            else (lambda p: p.read_text(encoding="utf-8"))
        )

    def collect(self) -> dict[str, Any]:
        socket_ok = self._exists(self._socket_path)
        in_container = self._exists(self._dockerenv_path)
        if not in_container and self._exists(self._cgroup_path):
            try:
                text = self._read_text(self._cgroup_path)
            except OSError:
                text = ""
            in_container = "docker" in text or "containerd" in text
        return {
            "available": socket_ok,
            "socket": str(self._socket_path) if socket_ok else None,
            "in_container": in_container,
        }
