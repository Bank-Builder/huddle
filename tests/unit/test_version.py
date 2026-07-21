"""Unit tests for package version metadata and CLI."""

from __future__ import annotations

from hudctl import __version__
from hudctl.cli.main import main


def test_version_is_semver_like() -> None:
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(part.isdigit() for part in parts[:2])


def test_cli_version_prints_package_version(capsys) -> None:
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == __version__


def test_cli_default_prints_version(capsys) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out.strip() == __version__
