"""Tests for daemon state IPC helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from hudctl.config import Config, ensure_dirs
from hudctl.daemon import (
    build_engine,
    format_status,
    is_pid_alive,
    is_running,
    pid_path,
    read_pid,
    read_state,
    restart_daemon,
    run_foreground,
    start_background,
    state_path,
    stop_daemon,
    write_state,
)


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def test_build_engine_registers_configured_modules(xdg_home: Path) -> None:
    _ = xdg_home
    engine = build_engine(Config(modules=("clock", "cwd")))
    names = {collector.name for collector in engine.collectors()}
    assert names == {"clock", "cwd"}


def test_build_engine_skips_unknown_modules(xdg_home: Path) -> None:
    _ = xdg_home
    engine = build_engine(Config(modules=("clock", "nope")))
    names = {collector.name for collector in engine.collectors()}
    assert names == {"clock"}


def test_write_and_read_state(xdg_home: Path) -> None:
    _ = xdg_home
    write_state({"clock": {"hhmm": "12:00"}}, pid=123)
    payload = read_state()
    assert payload is not None
    assert payload["pid"] == 123
    assert payload["sections"]["clock"]["hhmm"] == "12:00"


def test_format_status_not_running(xdg_home: Path) -> None:
    _ = xdg_home
    text, code = format_status()
    assert code == 1
    assert "not running" in text
    assert is_running() is False
    body, json_code = format_status(as_json=True)
    assert json_code == 1
    assert json.loads(body)["running"] is False


def test_run_foreground_with_immediate_stop(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = xdg_home

    async def fake_run(stop_event: Any, *, config: Config | None = None) -> None:
        _ = config
        stop_event.set()

    monkeypatch.setattr("hudctl.daemon.run_async", fake_run)
    assert run_foreground(config=Config(modules=("clock",))) == 0
    assert is_running() is False


def test_stop_daemon_not_running(xdg_home: Path) -> None:
    _ = xdg_home
    assert stop_daemon() == 0


def test_stop_daemon_sigterm(xdg_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = xdg_home
    alive = iter([True, False])
    monkeypatch.setattr("hudctl.daemon.read_pid", lambda: 4242)
    monkeypatch.setattr("hudctl.daemon.is_pid_alive", lambda _pid: next(alive))
    sent: list[int] = []
    monkeypatch.setattr(
        "hudctl.daemon.os.kill",
        lambda _pid, sig: sent.append(sig),
    )
    assert stop_daemon(timeout=1.0) == 0
    assert sent


def test_start_background_when_already_running(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = xdg_home
    monkeypatch.setattr("hudctl.daemon.is_running", lambda: True)
    assert start_background() == 0


def test_restart_daemon(xdg_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = xdg_home
    calls: list[str] = []
    monkeypatch.setattr(
        "hudctl.daemon.stop_daemon",
        lambda: calls.append("stop") or 0,
    )
    monkeypatch.setattr(
        "hudctl.daemon.start_background",
        lambda: calls.append("start") or 0,
    )
    assert restart_daemon() == 0
    assert calls == ["stop", "start"]


def test_is_pid_alive_missing() -> None:
    assert is_pid_alive(2_147_000_000) is False


def test_format_status_running(xdg_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = xdg_home
    write_state({"clock": {"hhmm": "01:02"}}, pid=99)
    monkeypatch.setattr("hudctl.daemon.is_running", lambda: True)
    monkeypatch.setattr("hudctl.daemon.read_pid", lambda: 99)
    text, code = format_status()
    assert code == 0
    assert "pid 99" in text
    assert "clock" in text
    body, json_code = format_status(as_json=True)
    assert json_code == 0
    assert json.loads(body)["running"] is True


def test_read_state_corrupt(xdg_home: Path) -> None:
    _ = xdg_home
    ensure_dirs()
    state_path().write_text("{not-json", encoding="utf-8")
    assert read_state() is None


def test_run_foreground_lock_failure(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = xdg_home

    def boom() -> Any:
        msg = "another hudctl daemon is already running"
        raise RuntimeError(msg)

    monkeypatch.setattr("hudctl.daemon._acquire_lock", boom)
    assert run_foreground() == 1


def test_stop_daemon_escalates_to_kill(
    xdg_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = xdg_home
    states = iter([True, True, True, False])
    monkeypatch.setattr("hudctl.daemon.read_pid", lambda: 4242)
    monkeypatch.setattr(
        "hudctl.daemon.is_pid_alive",
        lambda _pid: next(states, False),
    )
    monkeypatch.setattr("hudctl.daemon.time.sleep", lambda _s: None)
    sent: list[int] = []
    monkeypatch.setattr(
        "hudctl.daemon.os.kill",
        lambda _pid, sig: sent.append(sig),
    )
    assert stop_daemon(timeout=0.0) == 0
    assert len(sent) >= 2


def test_read_pid_invalid(xdg_home: Path) -> None:
    _ = xdg_home
    ensure_dirs()
    pid_path().write_text("not-a-pid\n", encoding="utf-8")
    assert read_pid() is None
