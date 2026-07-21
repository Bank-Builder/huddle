"""Tests for theme loading and formatter purity."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.formatter import format_line, format_segments
from hudctl.theme import default_theme, load_theme


def test_load_packaged_themes() -> None:
    developer = load_theme("developer")
    minimal = load_theme("minimal")
    assert developer.name == "developer"
    assert developer.show_cpu is True
    assert minimal.show_cpu is False
    assert default_theme().name == "developer"


def test_load_user_theme_override(tmp_path: Path) -> None:
    path = tmp_path / "custom.toml"
    path.write_text('separator = " :: "\nshow_clock = false\n', encoding="utf-8")
    theme = load_theme("custom", user_dir=tmp_path)
    assert theme.separator == " :: "
    assert theme.show_clock is False


def test_unknown_theme_raises() -> None:
    with pytest.raises(FileNotFoundError, match="unknown theme"):
        load_theme("does-not-exist")


def test_format_line_from_injected_state() -> None:
    state = {
        "cwd": {"display": "~/proj"},
        "git": {"inside_repo": True, "branch": "main", "dirty": True},
        "clock": {"hhmm": "12:00"},
        "cpu": {"percent": 12.3},
    }
    theme = load_theme("minimal")
    line = format_line(state, theme)
    assert line == "~/proj | main * | 12:00"
    assert format_segments(state, theme) == ["~/proj", "main *", "12:00"]


def test_format_developer_includes_resource_segments() -> None:
    state = {
        "cwd": {"display": "~/proj"},
        "git": {"inside_repo": True, "branch": "main", "dirty": False},
        "cpu": {"percent": 10},
        "memory": {"percent": 50.5},
        "network": {"rx_bps": 512, "tx_bps": 2048},
        "clock": {"hhmm": "08:00"},
    }
    theme = load_theme("developer")
    segments = format_segments(state, theme)
    assert any(seg.startswith("CPU ") for seg in segments)
    assert any(seg.startswith("MEM ") for seg in segments)
    assert any("↓" in seg and "↑" in seg for seg in segments)


def test_format_network_human_units() -> None:
    theme = load_theme("developer")
    small = format_segments(
        {"network": {"rx_bps": 100, "tx_bps": 200}},
        theme,
    )[0]
    medium = format_segments(
        {"network": {"rx_bps": 2048, "tx_bps": 4096}},
        theme,
    )[0]
    large = format_segments(
        {"network": {"rx_bps": 2_097_152, "tx_bps": 3_145_728}},
        theme,
    )[0]
    assert "100B" in small
    assert "2.0K" in medium
    assert "2.0M" in large
