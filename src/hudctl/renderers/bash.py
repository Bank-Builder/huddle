"""Bash PS1 fragment renderer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hudctl.formatter import format_line
from hudctl.renderers.base import Renderer
from hudctl.theme import Theme


def _bash_escape(text: str) -> str:
    """Escape characters that are special inside double-quoted PS1 values."""
    return (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("$", "\\$")
        .replace('"', '\\"')
    )


class BashRenderer(Renderer):
    """Render a one-line PS1 fragment from state."""

    name = "bash"

    def render(
        self,
        state: Mapping[str, Mapping[str, Any]],
        theme: Theme,
    ) -> str:
        line = format_line(state, theme)
        if not line:
            return "\\u@\\h:\\w\\$ "
        return f"{_bash_escape(line)}\\$ "
