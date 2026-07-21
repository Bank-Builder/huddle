"""Tests for GitCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.cache import DiskCache
from hudctl.collectors.git import GitCollector


def test_git_collector_outside_repo(tmp_path: Path) -> None:
    data = GitCollector(getcwd=lambda: str(tmp_path)).collect()
    assert data["inside_repo"] is False
    assert data["branch"] is None


def test_git_collector_reads_branch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    git = repo / ".git"
    git.mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/feature\n", encoding="utf-8")

    data = GitCollector(getcwd=lambda: str(repo)).collect()
    assert data["inside_repo"] is True
    assert data["branch"] == "feature"
    assert data["root"] == str(repo)


def test_git_collector_uses_cache(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    git = repo / ".git"
    git.mkdir(parents=True)
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    cache = DiskCache(tmp_path / "cache")
    collector = GitCollector(getcwd=lambda: str(repo), cache=cache, cache_ttl=60)
    first = collector.collect()
    (git / "HEAD").write_text("ref: refs/heads/other\n", encoding="utf-8")
    second = collector.collect()
    assert first == second
    assert second["branch"] == "main"
