"""Tests for install/uninstall helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.cli.install import (
    BEGIN_MARKER,
    END_MARKER,
    install,
    install_bash_snippet,
    render_unit,
    uninstall,
    uninstall_bash_snippet,
)
from hudctl.cli.main import main


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    return tmp_path


def test_render_unit_includes_exec_start() -> None:
    text = render_unit(exec_start="/usr/bin/hudctl run")
    assert "ExecStart=/usr/bin/hudctl run" in text
    assert "[Service]" in text


def test_bash_snippet_idempotent(tmp_path: Path) -> None:
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text("export FOO=1\n", encoding="utf-8")
    first = install_bash_snippet(path=bashrc)
    second = install_bash_snippet(path=bashrc)
    content = bashrc.read_text(encoding="utf-8")
    assert content.count(BEGIN_MARKER) == 1
    assert content.count(END_MARKER) == 1
    assert "export FOO=1" in content
    assert "updated" in first
    assert "unchanged" in second


def test_bash_snippet_uninstall(tmp_path: Path) -> None:
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text("before\n", encoding="utf-8")
    install_bash_snippet(path=bashrc)
    uninstall_bash_snippet(path=bashrc)
    content = bashrc.read_text(encoding="utf-8")
    assert BEGIN_MARKER not in content
    assert END_MARKER not in content
    assert "before" in content


def test_install_twice_no_duplicate_unit(xdg_home: Path) -> None:
    unit = xdg_home / "config" / "systemd" / "user" / "huddle.service"
    bashrc = xdg_home / "home" / ".bashrc"
    first = install(bashrc=bashrc, unit=unit)
    second = install(bashrc=bashrc, unit=unit)
    assert unit.is_file()
    assert unit.read_text(encoding="utf-8").count("[Service]") == 1
    assert any("written" in action or "unchanged" in action for action in first.actions)
    assert any("unchanged" in action for action in second.actions)


def test_uninstall_removes_unit_keeps_config(xdg_home: Path) -> None:
    unit = xdg_home / "config" / "systemd" / "user" / "huddle.service"
    bashrc = xdg_home / "home" / ".bashrc"
    install(bashrc=bashrc, unit=unit)
    config = xdg_home / "config" / "huddle" / "config.toml"
    assert config.is_file()
    uninstall(bashrc=bashrc, unit=unit)
    assert not unit.exists()
    assert config.is_file()


def test_cli_install_uninstall(
    xdg_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = xdg_home
    assert main(["install"]) == 0
    out = capsys.readouterr().out
    assert "hudctl install" in out
    assert main(["uninstall"]) == 0
    assert "hudctl uninstall" in capsys.readouterr().out
