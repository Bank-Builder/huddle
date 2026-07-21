"""TTL disk cache under the huddle XDG cache directory."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.config import cache_dir


class DiskCache:
    """Simple JSON file cache with per-entry TTL."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._root = root if root is not None else cache_dir() / "entries"
        self._clock = clock if clock is not None else time.monotonic

    def _path_for(self, key: str) -> Path:
        safe = key.replace("/", "_").replace("..", "_")
        return self._root / f"{safe}.json"

    def get(self, key: str) -> Any | None:
        """Return cached value if present and not expired."""
        path = self._path_for(key)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        expires_at = payload.get("expires_at")
        value = payload.get("value")
        if not isinstance(expires_at, int | float):
            return None
        if self._clock() >= float(expires_at):
            path.unlink(missing_ok=True)
            return None
        return value

    def set(self, key: str, value: Any, *, ttl: float) -> None:
        """Store ``value`` under ``key`` for ``ttl`` seconds."""
        if ttl <= 0:
            msg = "ttl must be positive"
            raise ValueError(msg)
        self._root.mkdir(parents=True, mode=0o700, exist_ok=True)
        payload = {
            "expires_at": self._clock() + float(ttl),
            "value": value,
        }
        path = self._path_for(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        tmp.replace(path)

    def delete(self, key: str) -> None:
        """Remove a cache entry if it exists."""
        self._path_for(key).unlink(missing_ok=True)

    def clear(self) -> None:
        """Remove all cache entries under this cache root."""
        if not self._root.is_dir():
            return
        for path in self._root.glob("*.json"):
            path.unlink(missing_ok=True)
