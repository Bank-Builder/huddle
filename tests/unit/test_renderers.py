"""Tests for pure renderers with injected state."""

from __future__ import annotations

import json

from hudctl.renderers.bash import BashRenderer
from hudctl.renderers.json import JsonRenderer
from hudctl.renderers.kitty import KittyRenderer
from hudctl.theme import load_theme

STATE = {
    "cwd": {"display": "~/proj"},
    "git": {"inside_repo": True, "branch": "main", "dirty": False},
    "clock": {"hhmm": "09:30"},
}


def test_json_renderer_golden() -> None:
    theme = load_theme("minimal")
    out = JsonRenderer().render(STATE, theme)
    payload = json.loads(out)
    assert payload["theme"] == "minimal"
    assert payload["line"] == "~/proj | main | 09:30"
    assert payload["sections"]["git"]["branch"] == "main"


def test_bash_renderer_golden() -> None:
    theme = load_theme("minimal")
    out = BashRenderer().render(STATE, theme)
    assert out == "~/proj | main | 09:30\\$ "


def test_bash_renderer_empty_state_fallback() -> None:
    theme = load_theme("minimal")
    out = BashRenderer().render({}, theme)
    assert out == "\\u@\\h:\\w\\$ "


def test_bash_renderer_escapes_specials() -> None:
    theme = load_theme("minimal")
    state = {"cwd": {"display": 'path/$`"'}}
    out = BashRenderer().render(state, theme)
    assert "\\$" in out
    assert "\\`" in out
    assert '\\"' in out


def test_kitty_renderer_remote_and_ansi() -> None:
    theme = load_theme("minimal")
    remote = KittyRenderer(prefer_remote_control=True).render(STATE, theme)
    assert remote.startswith("set-window-title ")
    assert "set-tab-title " in remote
    ansi = KittyRenderer(prefer_remote_control=False).render(STATE, theme)
    assert "\033]0;" in ansi
    assert "\033]2;" in ansi
