"""Kubernetes context collector (kubeconfig scrape, no kubectl)."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from hudctl.collectors.base import Collector


def _default_kubeconfig(environ: Mapping[str, str]) -> Path | None:
    override = environ.get("KUBECONFIG")
    if override:
        # Use the first path if a list is provided.
        first = override.split(":", 1)[0].strip()
        return Path(first).expanduser() if first else None
    home = environ.get("HOME") or str(Path.home())
    return Path(home) / ".kube" / "config"


def _parse_current_context(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("current-context:"):
            value = stripped.split(":", 1)[1].strip().strip("\"'")
            return value or None
    return None


class KubernetesCollector(Collector):
    """Report kubeconfig presence and current-context without kubectl."""

    name = "kubernetes"
    interval = 20.0

    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        kubeconfig: Path | None = None,
        read_text: Callable[[Path], str] | None = None,
    ) -> None:
        self._environ: Mapping[str, str] = (
            environ if environ is not None else os.environ
        )
        self._kubeconfig = kubeconfig
        self._read_text = (
            read_text if read_text is not None else (lambda p: p.read_text(encoding="utf-8"))
        )

    def collect(self) -> dict[str, Any]:
        path = self._kubeconfig
        if path is None:
            path = _default_kubeconfig(self._environ)
        in_cluster = bool(self._environ.get("KUBERNETES_SERVICE_HOST"))
        if path is None or not path.is_file():
            return {
                "available": False,
                "kubeconfig": str(path) if path else None,
                "context": None,
                "in_cluster": in_cluster,
            }
        try:
            text = self._read_text(path)
            context = _parse_current_context(text)
        except OSError:
            context = None
        return {
            "available": True,
            "kubeconfig": str(path),
            "context": context,
            "in_cluster": in_cluster,
        }
