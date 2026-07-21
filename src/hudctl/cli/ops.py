"""Theme and config operator commands."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from hudctl.config import Config, config_dir, config_path, load_config, save_config
from hudctl.theme import list_themes, load_theme


def themes_dir() -> Path:
    """Return the user theme override directory."""
    return config_dir() / "themes"


def theme_list_text() -> str:
    """Return a formatted list of available themes."""
    current = load_config().theme
    names = list_themes(user_dir=themes_dir())
    lines = ["themes:"]
    for name in names:
        marker = "*" if name == current else " "
        lines.append(f" {marker} {name}")
    return "\n".join(lines)


def theme_set(name: str) -> tuple[str, int]:
    """Set the active theme in config.toml after validating it exists."""
    try:
        load_theme(name, user_dir=themes_dir())
    except FileNotFoundError:
        return f"unknown theme: {name}", 1
    cfg = load_config()
    updated = Config(
        theme=name,
        refresh=cfg.refresh,
        log_level=cfg.log_level,
        renderers=cfg.renderers,
        modules=cfg.modules,
    )
    path = save_config(updated)
    return f"theme set to {name} ({path})", 0


def config_edit(*, editor: str | None = None) -> int:
    """Open the user config file in ``$EDITOR`` (or nano)."""
    path = config_path()
    if not path.is_file():
        save_config(load_config())
    program = editor or os.environ.get("EDITOR") or "nano"
    return subprocess.call([program, str(path)])  # noqa: S603
