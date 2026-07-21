"""Integration tests for daemon start/status/stop."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest

from hudctl.cli.main import main
from hudctl.config import Config
from hudctl.daemon import (
    is_running,
    read_state,
    run_async,
    start_background,
    stop_daemon,
)


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def test_run_async_writes_sections(xdg_home: Path) -> None:
    _ = xdg_home

    async def _run() -> None:
        stop = asyncio.Event()

        async def stop_soon() -> None:
            await asyncio.sleep(0.05)
            stop.set()

        await asyncio.gather(
            run_async(stop, config=Config(modules=("clock", "cwd"))),
            stop_soon(),
        )

    asyncio.run(_run())
    payload = read_state()
    assert payload is not None
    assert "clock" in payload["sections"]
    assert "cwd" in payload["sections"]


def test_start_status_stop_lifecycle(xdg_home: Path) -> None:
    _ = xdg_home
    config_dir = xdg_home / "config" / "huddle"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        'modules = ["clock", "cwd"]\n',
        encoding="utf-8",
    )

    try:
        assert start_background() == 0
        deadline = time.monotonic() + 5
        payload = None
        while time.monotonic() < deadline:
            if is_running():
                payload = read_state()
                if payload and payload.get("sections"):
                    break
            time.sleep(0.05)
        assert is_running()
        assert payload is not None
        assert "clock" in payload["sections"]

        assert main(["status"]) == 0
        assert main(["status", "--json"]) == 0
    finally:
        assert stop_daemon(timeout=2.0) == 0
        assert is_running() is False


def test_status_json_shape_when_running(
    xdg_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = xdg_home
    config_dir = xdg_home / "config" / "huddle"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        'modules = ["clock"]\n',
        encoding="utf-8",
    )
    try:
        assert main(["start"]) == 0
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not is_running():
            time.sleep(0.05)
        capsys.readouterr()
        assert main(["status", "--json"]) == 0
        body = json.loads(capsys.readouterr().out)
        assert body["running"] is True
        assert "clock" in body["sections"]
    finally:
        assert main(["stop"]) == 0
