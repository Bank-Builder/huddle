"""JSON renderer for scripts and tooling."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from hudctl.renderers.base import Renderer
from hudctl.theme import Theme


class JsonRenderer(Renderer):
    """Serialize state (and theme name) as JSON."""

    name = "json"

    def render(
        self,
        state: Mapping[str, Mapping[str, Any]],
        theme: Theme,
    ) -> str:
        payload = {
            "theme": theme.name,
            "sections": dict(state),
            "line": None,
        }
        # Import locally to keep renderer free of circular imports at module load.
        from hudctl.formatter import format_line

        payload["line"] = format_line(state, theme)
        return json.dumps(payload, indent=2, sort_keys=True)
