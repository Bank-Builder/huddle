"""Tests for ContextState sectional updates."""

from __future__ import annotations

from hudctl.state import ContextState


def test_with_section_replaces_and_isolates_mutations() -> None:
    state = ContextState()
    updated = state.with_section("git", {"branch": "main", "dirty": False})
    assert state.get("git") is None
    section = updated.get("git")
    assert section == {"branch": "main", "dirty": False}
    assert section is not None
    section["dirty"] = True
    assert updated.get("git") == {"branch": "main", "dirty": False}


def test_snapshot_is_deep_copy() -> None:
    state = ContextState().with_section("cpu", {"percent": 10})
    snap = state.snapshot()
    snap["cpu"]["percent"] = 99
    assert state.get("cpu") == {"percent": 10}


def test_without_section() -> None:
    state = (
        ContextState()
        .with_section("a", {"x": 1})
        .with_section("b", {"y": 2})
        .without_section("a")
    )
    assert state.names() == frozenset({"b"})
    assert state.without_section("missing") is state
