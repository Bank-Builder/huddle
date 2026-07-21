"""Tests for CwdCollector."""

from __future__ import annotations

from pathlib import Path

from hudctl.collectors.cwd import CwdCollector


def test_cwd_collector_under_home(tmp_path: Path) -> None:
    home = tmp_path / "home"
    project = home / "proj"
    project.mkdir(parents=True)

    data = CwdCollector(
        getcwd=lambda: str(project),
        home=lambda: home,
    ).collect()

    assert data["path"] == str(project.resolve())
    assert data["display"] == "~/proj"
    assert data["basename"] == "proj"


def test_cwd_collector_outside_home(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    other = tmp_path / "other"
    other.mkdir()

    data = CwdCollector(
        getcwd=lambda: str(other),
        home=lambda: home,
    ).collect()

    assert data["display"] == str(other.resolve())
