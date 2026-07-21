"""Kitty title renderer (remote-control style and ANSI fallback)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hudctl.formatter import format_line
from hudctl.renderers.base import Renderer
from hudctl.theme import Theme


class KittyRenderer(Renderer):
    """Render Kitty window/tab title update sequences.

    Pure string output only. Callers decide whether to write to Kitty remote
    control or emit ANSI OSC escapes.
    """

    name = "kitty"

    def __init__(self, *, prefer_remote_control: bool = True) -> None:
        self._prefer_remote_control = prefer_remote_control

    def render(
        self,
        state: Mapping[str, Mapping[str, Any]],
        theme: Theme,
    ) -> str:
        title = format_line(state, theme) or "huddle"
        if self._prefer_remote_control:
            # Kitty remote control protocol (literal command text).
            return f"set-window-title {title}\nset-tab-title {title}\n"
        # ANSI OSC 0 / 2 title sequences.
        return f"\033]0;{title}\007\033]2;{title}\007"
