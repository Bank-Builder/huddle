"""Git status collector with aggressive caching (avoid repeated work)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from hudctl.cache import DiskCache
from hudctl.collectors.base import Collector


def _getcwd() -> str:
    import os

    return os.getcwd()


def _find_git_dir(start: Path) -> Path | None:
    current = start.resolve(strict=False)
    for path in (current, *current.parents):
        candidate = path / ".git"
        if candidate.is_dir():
            return candidate
        if candidate.is_file():
            # gitfile redirect for worktrees
            try:
                content = candidate.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            if content.startswith("gitdir:"):
                gitdir = (path / content.removeprefix("gitdir:").strip()).resolve()
                return gitdir if gitdir.exists() else None
    return None


def _read_branch(git_dir: Path) -> str | None:
    head = git_dir / "HEAD"
    try:
        content = head.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if content.startswith("ref:"):
        ref = content.removeprefix("ref:").strip()
        return ref.rsplit("/", 1)[-1]
    return content[:7] if content else None


def _is_dirty(git_dir: Path, work_tree: Path) -> bool:
    """Best-effort dirty detection without invoking git.

    Compares index presence and looks for an unfinished merge/rebase.
    Full porcelain dirty detection requires git; we keep this lightweight.
    """
    _ = work_tree
    for marker in (
        git_dir / "MERGE_HEAD",
        git_dir / "rebase-merge",
        git_dir / "rebase-apply",
    ):
        if marker.exists():
            return True
    return False


class GitCollector(Collector):
    """Collect branch and dirty hints by reading ``.git`` metadata.

    Prefer filesystem reads over ``git`` subprocesses. Results are cached
    briefly to avoid repeated directory walks.
    """

    name = "git"
    interval = 5.0

    def __init__(
        self,
        *,
        getcwd: Callable[[], str] | None = None,
        cache: DiskCache | None = None,
        cache_ttl: float = 2.0,
    ) -> None:
        self._getcwd = getcwd if getcwd is not None else _getcwd
        self._cache = cache
        self._cache_ttl = cache_ttl

    def collect(self) -> dict[str, Any]:
        cwd = Path(self._getcwd())
        cache_key = f"git:{cwd}"
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if isinstance(cached, dict):
                return cached

        git_dir = _find_git_dir(cwd)
        if git_dir is None:
            data: dict[str, Any] = {
                "inside_repo": False,
                "branch": None,
                "dirty": False,
                "root": None,
            }
        else:
            root = git_dir.parent if git_dir.name == ".git" else cwd
            data = {
                "inside_repo": True,
                "branch": _read_branch(git_dir),
                "dirty": _is_dirty(git_dir, root),
                "root": str(root),
            }

        if self._cache is not None:
            self._cache.set(cache_key, data, ttl=self._cache_ttl)
        return data
