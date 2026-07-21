"""Theme loading for huddle renderers."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Theme:
    """Display tokens and section visibility for renderers."""

    name: str
    separator: str = " | "
    cwd_icon: str = ""
    git_icon: str = ""
    clock_icon: str = ""
    cpu_icon: str = ""
    memory_icon: str = ""
    network_icon: str = ""
    show_cwd: bool = True
    show_git: bool = True
    show_clock: bool = True
    show_cpu: bool = False
    show_memory: bool = False
    show_network: bool = False


def _theme_from_mapping(name: str, data: dict[str, object]) -> Theme:
    def _str(key: str, default: str) -> str:
        value = data.get(key, default)
        return value if isinstance(value, str) else default

    def _bool(key: str, default: bool) -> bool:
        value = data.get(key, default)
        return value if isinstance(value, bool) else default

    return Theme(
        name=name,
        separator=_str("separator", " | "),
        cwd_icon=_str("cwd_icon", ""),
        git_icon=_str("git_icon", ""),
        clock_icon=_str("clock_icon", ""),
        cpu_icon=_str("cpu_icon", ""),
        memory_icon=_str("memory_icon", ""),
        network_icon=_str("network_icon", ""),
        show_cwd=_bool("show_cwd", True),
        show_git=_bool("show_git", True),
        show_clock=_bool("show_clock", True),
        show_cpu=_bool("show_cpu", False),
        show_memory=_bool("show_memory", False),
        show_network=_bool("show_network", False),
    )


def load_theme(name: str, *, user_dir: Path | None = None) -> Theme:
    """Load a theme by name from user dir, then packaged themes."""
    if user_dir is not None:
        user_path = user_dir / f"{name}.toml"
        if user_path.is_file():
            with user_path.open("rb") as handle:
                return _theme_from_mapping(name, tomllib.load(handle))

    packaged = resources.files("hudctl.themes").joinpath(f"{name}.toml")
    if packaged.is_file():
        with packaged.open("rb") as handle:
            return _theme_from_mapping(name, tomllib.load(handle))

    msg = f"unknown theme: {name}"
    raise FileNotFoundError(msg)


def list_themes(*, user_dir: Path | None = None) -> tuple[str, ...]:
    """Return sorted theme names from packaged and user theme dirs."""
    names: set[str] = set()
    packaged = resources.files("hudctl.themes")
    for entry in packaged.iterdir():
        if entry.name.endswith(".toml"):
            names.add(entry.name.removesuffix(".toml"))
    directory = user_dir
    if directory is not None and directory.is_dir():
        for path in directory.glob("*.toml"):
            names.add(path.stem)
    return tuple(sorted(names))


def default_theme() -> Theme:
    """Return the packaged developer theme."""
    return load_theme("developer")
