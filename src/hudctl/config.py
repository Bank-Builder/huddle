"""XDG path helpers and configuration loading for hudctl."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

APP_NAME = "huddle"


@dataclass(frozen=True, slots=True)
class Config:
    """User and default configuration for the huddle daemon."""

    theme: str = "developer"
    refresh: float = 1.0
    renderers: tuple[str, ...] = ("kitty", "bash")
    modules: tuple[str, ...] = (
        "cwd",
        "git",
        "cpu",
        "memory",
        "network",
        "clock",
    )


def _xdg_home(env_var: str, default_subdir: str) -> Path:
    """Resolve an XDG base directory from the environment."""
    override = os.environ.get(env_var)
    if override:
        return Path(override).expanduser()
    return Path.home() / default_subdir


def config_dir() -> Path:
    """Return the user config directory (~/.config/huddle)."""
    return _xdg_home("XDG_CONFIG_HOME", ".config") / APP_NAME


def cache_dir() -> Path:
    """Return the user cache directory (~/.cache/huddle)."""
    return _xdg_home("XDG_CACHE_HOME", ".cache") / APP_NAME


def state_dir() -> Path:
    """Return the user state directory (~/.local/state/huddle)."""
    return _xdg_home("XDG_STATE_HOME", ".local/state") / APP_NAME


def config_path() -> Path:
    """Return the path to the user config.toml."""
    return config_dir() / "config.toml"


def ensure_dirs() -> None:
    """Create config, cache, and state directories if missing."""
    for path in (config_dir(), cache_dir(), state_dir()):
        path.mkdir(parents=True, mode=0o700, exist_ok=True)


def default_config() -> Config:
    """Return the built-in default configuration."""
    return Config()


def _as_str_tuple(value: Any, *, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        msg = f"{field_name} must be a list of strings"
        raise ValueError(msg)
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            msg = f"{field_name} must be a list of strings"
            raise ValueError(msg)
        items.append(item)
    return tuple(items)


def config_from_mapping(data: dict[str, Any]) -> Config:
    """Build a Config from a parsed TOML mapping, merging with defaults."""
    base = default_config()
    updates: dict[str, Any] = {}

    if "theme" in data:
        theme = data["theme"]
        if not isinstance(theme, str):
            msg = "theme must be a string"
            raise ValueError(msg)
        updates["theme"] = theme

    if "refresh" in data:
        refresh = data["refresh"]
        if isinstance(refresh, bool) or not isinstance(refresh, int | float):
            msg = "refresh must be a number"
            raise ValueError(msg)
        updates["refresh"] = float(refresh)

    if "renderers" in data:
        updates["renderers"] = _as_str_tuple(data["renderers"], field_name="renderers")

    if "modules" in data:
        updates["modules"] = _as_str_tuple(data["modules"], field_name="modules")

    return replace(base, **updates)


def load_config(path: Path | None = None) -> Config:
    """Load config from disk, or return defaults if the file is missing."""
    cfg_path = path if path is not None else config_path()
    if not cfg_path.is_file():
        return default_config()

    with cfg_path.open("rb") as handle:
        data = tomllib.load(handle)

    return config_from_mapping(data)


def save_config(config: Config, path: Path | None = None) -> Path:
    """Write config to TOML and return the path written."""
    cfg_path = path if path is not None else config_path()
    cfg_path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)

    lines = [
        f'theme = "{config.theme}"',
        f"refresh = {config.refresh:g}",
        "",
        "renderers = [",
        *[f'    "{name}",' for name in config.renderers],
        "]",
        "",
        "modules = [",
        *[f'    "{name}",' for name in config.modules],
        "]",
        "",
    ]
    cfg_path.write_text("\n".join(lines), encoding="utf-8")
    return cfg_path
