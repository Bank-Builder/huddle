"""Pure formatting helpers that turn state sections into display segments."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hudctl.theme import Theme


def _cwd_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_cwd:
        return None
    display = section.get("display") or section.get("basename") or section.get("path")
    if not isinstance(display, str) or not display:
        return None
    return f"{theme.cwd_icon}{display}"


def _git_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_git or not section.get("inside_repo"):
        return None
    branch = section.get("branch")
    if not isinstance(branch, str) or not branch:
        return None
    dirty = " *" if section.get("dirty") else ""
    return f"{theme.git_icon}{branch}{dirty}"


def _clock_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_clock:
        return None
    hhmm = section.get("hhmm")
    if not isinstance(hhmm, str) or not hhmm:
        return None
    return f"{theme.clock_icon}{hhmm}"


def _cpu_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_cpu:
        return None
    percent = section.get("percent")
    if not isinstance(percent, int | float):
        return None
    return f"{theme.cpu_icon}{percent:.0f}%"


def _memory_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_memory:
        return None
    percent = section.get("percent")
    if not isinstance(percent, int | float):
        return None
    return f"{theme.memory_icon}{percent:.0f}%"


def _network_segment(section: Mapping[str, Any], theme: Theme) -> str | None:
    if not theme.show_network:
        return None
    rx = section.get("rx_bps")
    tx = section.get("tx_bps")
    if not isinstance(rx, int | float) or not isinstance(tx, int | float):
        return None
    return f"{theme.network_icon}↓{_human_bps(rx)} ↑{_human_bps(tx)}"


def _human_bps(value: float) -> str:
    if value < 1024:
        return f"{value:.0f}B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f}K"
    return f"{value / (1024 * 1024):.1f}M"


_SEGMENTERS = (
    ("cwd", _cwd_segment),
    ("git", _git_segment),
    ("cpu", _cpu_segment),
    ("memory", _memory_segment),
    ("network", _network_segment),
    ("clock", _clock_segment),
)


def format_segments(
    state: Mapping[str, Mapping[str, Any]],
    theme: Theme,
) -> list[str]:
    """Build ordered non-empty display segments from state."""
    segments: list[str] = []
    for name, segmenter in _SEGMENTERS:
        section = state.get(name)
        if not isinstance(section, Mapping):
            continue
        segment = segmenter(section, theme)
        if segment:
            segments.append(segment)
    return segments


def format_line(
    state: Mapping[str, Mapping[str, Any]],
    theme: Theme,
) -> str:
    """Join formatted segments with the theme separator."""
    return theme.separator.join(format_segments(state, theme))
