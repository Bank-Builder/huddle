"""Tests for XDG paths and configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.config import (
    Config,
    config_from_mapping,
    config_path,
    default_config,
    ensure_dirs,
    load_config,
    save_config,
)


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def test_default_config_values() -> None:
    cfg = default_config()
    assert cfg.theme == "developer"
    assert cfg.refresh == 1.0
    assert "git" in cfg.modules
    assert "kitty" in cfg.renderers


def test_load_config_missing_returns_defaults(xdg_home: Path) -> None:
    _ = xdg_home
    assert load_config() == default_config()


def test_load_and_save_config_roundtrip(xdg_home: Path) -> None:
    _ = xdg_home
    ensure_dirs()
    original = Config(
        theme="minimal",
        refresh=2.5,
        renderers=("bash",),
        modules=("cwd", "clock"),
    )
    path = save_config(original)
    assert path == config_path()
    assert path.is_file()
    assert load_config() == original


def test_config_from_mapping_partial_merge() -> None:
    cfg = config_from_mapping({"theme": "compact"})
    assert cfg.theme == "compact"
    assert cfg.modules == default_config().modules


def test_config_from_mapping_rejects_bad_types() -> None:
    with pytest.raises(ValueError, match="theme"):
        config_from_mapping({"theme": 1})
    with pytest.raises(ValueError, match="refresh"):
        config_from_mapping({"refresh": True})
    with pytest.raises(ValueError, match="renderers"):
        config_from_mapping({"renderers": "bash"})
    with pytest.raises(ValueError, match="modules"):
        config_from_mapping({"modules": [1]})


def test_ensure_dirs_creates_xdg_tree(xdg_home: Path) -> None:
    ensure_dirs()
    assert (xdg_home / "config" / "huddle").is_dir()
    assert (xdg_home / "cache" / "huddle").is_dir()
    assert (xdg_home / "state" / "huddle").is_dir()
