"""Tests for EventBus pub/sub."""

from __future__ import annotations

from hudctl.events import EventBus, SectionUpdated


def test_subscribe_section_and_all() -> None:
    bus = EventBus()
    seen: list[str] = []

    def on_git(event: SectionUpdated) -> None:
        seen.append(f"git:{event.data['branch']}")

    def on_any(event: SectionUpdated) -> None:
        seen.append(f"any:{event.section}")

    bus.subscribe("git", on_git)
    bus.subscribe_all(on_any)
    bus.emit(SectionUpdated("git", {"branch": "main"}))
    bus.emit(SectionUpdated("cpu", {"percent": 1}))
    assert seen == ["git:main", "any:git", "any:cpu"]


def test_unsubscribe() -> None:
    bus = EventBus()
    seen: list[str] = []

    def listener(event: SectionUpdated) -> None:
        seen.append(event.section)

    bus.subscribe("git", listener)
    bus.subscribe_all(listener)
    bus.unsubscribe("git", listener)
    bus.unsubscribe_all(listener)
    bus.unsubscribe("git", listener)
    bus.unsubscribe_all(listener)
    bus.emit(SectionUpdated("git", {}))
    assert seen == []
    bus.clear()
