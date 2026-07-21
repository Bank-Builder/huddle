"""Tests for theme/config operator commands and reload."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.cli.main import main
from hudctl.cli.ops import config_edit, theme_list_text, theme_set
from hudctl.config import load_config
from hudctl.daemon import reload_daemon


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def test_theme_list_and_set(xdg_home: Path) -> None:
    _ = xdg_home
    text = theme_list_text()
    assert "developer" in text
    assert "minimal" in text
    msg, code = theme_set("minimal")
    assert code == 0
    assert "minimal" in msg
    assert load_config().theme == "minimal"
    bad, bad_code = theme_set("nope")
    assert bad_code == 1
    assert "unknown" in bad


def test_cli_theme_commands(xdg_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _ = xdg_home
    assert main(["theme", "list"]) == 0
    assert "developer" in capsys.readouterr().out
    assert main(["theme", "set", "minimal"]) == 0
    assert load_config().theme == "minimal"


def test_config_edit_invokes_editor(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = xdg_home
    called: list[list[str]] = []

    def fake_call(cmd: list[str]) -> int:
        called.append(cmd)
        return 0

    monkeypatch.setattr("hudctl.cli.ops.subprocess.call", fake_call)
    assert config_edit(editor="true") == 0
    assert called[0][0] == "true"


def test_reload_requires_running_daemon(xdg_home: Path) -> None:
    _ = xdg_home
    assert reload_daemon() == 1


def test_cli_reload_not_running(xdg_home: Path) -> None:
    _ = xdg_home
    assert main(["reload"]) == 1
