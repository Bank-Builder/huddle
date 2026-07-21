"""Tests for DiskCache TTL behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.cache import DiskCache


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


def test_set_get_and_expire(tmp_path: Path) -> None:
    clock = FakeClock()
    cache = DiskCache(tmp_path / "entries", clock=clock)
    cache.set("git", {"branch": "main"}, ttl=10)
    assert cache.get("git") == {"branch": "main"}
    clock.now = 10
    assert cache.get("git") is None


def test_ttl_must_be_positive(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path / "entries")
    with pytest.raises(ValueError, match="ttl"):
        cache.set("x", 1, ttl=0)


def test_delete_and_clear(tmp_path: Path) -> None:
    cache = DiskCache(tmp_path / "entries")
    cache.set("a", 1, ttl=60)
    cache.set("b", 2, ttl=60)
    cache.delete("a")
    assert cache.get("a") is None
    assert cache.get("b") == 2
    cache.clear()
    assert cache.get("b") is None


def test_corrupt_payload_returns_none(tmp_path: Path) -> None:
    root = tmp_path / "entries"
    root.mkdir()
    (root / "bad.json").write_text("not-json", encoding="utf-8")
    cache = DiskCache(root)
    assert cache.get("bad") is None
