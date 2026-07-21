"""Daemon process lifecycle, PID lock, and state-file IPC."""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, TextIO

from hudctl.collectors.base import Collector
from hudctl.collectors.battery import BatteryCollector
from hudctl.collectors.clock import ClockCollector
from hudctl.collectors.cpu import CpuCollector
from hudctl.collectors.cwd import CwdCollector
from hudctl.collectors.docker import DockerCollector
from hudctl.collectors.git import GitCollector
from hudctl.collectors.hostname import HostnameCollector
from hudctl.collectors.kubernetes import KubernetesCollector
from hudctl.collectors.memory import MemoryCollector
from hudctl.collectors.network import NetworkCollector
from hudctl.collectors.ssh import SshCollector
from hudctl.collectors.vpn import VpnCollector
from hudctl.config import Config, ensure_dirs, load_config, state_dir
from hudctl.engine import Engine
from hudctl.events import SectionUpdated
from hudctl.scheduler import Scheduler

logger = logging.getLogger(__name__)

_COLLECTORS: dict[str, type[Collector]] = {
    "clock": ClockCollector,
    "cwd": CwdCollector,
    "cpu": CpuCollector,
    "memory": MemoryCollector,
    "network": NetworkCollector,
    "git": GitCollector,
    "hostname": HostnameCollector,
    "ssh": SshCollector,
    "docker": DockerCollector,
    "kubernetes": KubernetesCollector,
    "battery": BatteryCollector,
    "vpn": VpnCollector,
}


def pid_path() -> Path:
    """Return the daemon PID file path."""
    return state_dir() / "hudctl.pid"


def state_path() -> Path:
    """Return the shared state snapshot path."""
    return state_dir() / "state.json"


def lock_path() -> Path:
    """Return the single-instance lock file path."""
    return state_dir() / "hudctl.lock"


def read_pid() -> int | None:
    """Read the PID file, or None if missing/invalid."""
    path = pid_path()
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
        return int(text)
    except (OSError, ValueError):
        return None


def is_pid_alive(pid: int) -> bool:
    """Return True if ``pid`` exists and is not a zombie."""
    status_path = Path(f"/proc/{pid}/status")
    if status_path.is_file():
        try:
            for line in status_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("State:"):
                    state = line.split()[1]
                    return state != "Z"
        except OSError:
            return False
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def is_running() -> bool:
    """Return True if a live daemon owns the PID file."""
    pid = read_pid()
    return pid is not None and is_pid_alive(pid)


def write_state(snapshot: dict[str, dict[str, Any]], *, pid: int | None = None) -> None:
    """Atomically write the shared state snapshot."""
    ensure_dirs()
    payload = {
        "pid": pid if pid is not None else os.getpid(),
        "updated_at": time.time(),
        "sections": snapshot,
    }
    path = state_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(path)


def read_state() -> dict[str, Any] | None:
    """Read the shared state snapshot, or None if unavailable."""
    path = state_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def build_engine(config: Config | None = None) -> Engine:
    """Create an engine with collectors enabled by config modules."""
    cfg = config if config is not None else load_config()
    engine = Engine()
    for name in cfg.modules:
        collector_type = _COLLECTORS.get(name)
        if collector_type is None:
            logger.warning("unknown module in config: %s", name)
            continue
        engine.register(collector_type())
    return engine


def _acquire_lock() -> TextIO:
    ensure_dirs()
    handle = lock_path().open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        msg = "another hudctl daemon is already running"
        raise RuntimeError(msg) from exc
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def _write_pid() -> None:
    ensure_dirs()
    pid_path().write_text(f"{os.getpid()}\n", encoding="utf-8")


def _clear_pid() -> None:
    pid_path().unlink(missing_ok=True)


async def run_async(
    stop_event: asyncio.Event,
    *,
    config: Config | None = None,
) -> None:
    """Run the collector engine until ``stop_event`` is set."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    engine = build_engine(config)
    scheduler = Scheduler(engine)

    def on_update(_event: SectionUpdated) -> None:
        write_state(engine.snapshot())

    def on_reload() -> None:
        logger.info("reload requested; refreshing collectors")
        engine.collect_all()
        write_state(engine.snapshot())

    with contextlib.suppress(NotImplementedError):
        loop.add_signal_handler(signal.SIGHUP, on_reload)

    engine.bus.subscribe_all(on_update)
    # Seed state immediately so status works before the first interval tick.
    engine.collect_all()
    write_state(engine.snapshot())
    await scheduler.run(stop_event)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging for the daemon process."""
    resolved = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_foreground(*, config: Config | None = None) -> int:
    """Run the daemon in the foreground until SIGTERM/SIGINT."""
    lock: TextIO | None = None
    stop_event = asyncio.Event()
    cfg = config if config is not None else load_config()
    env_level = os.environ.get("HUDCTL_LOG_LEVEL")
    configure_logging(env_level or cfg.log_level)

    try:
        lock = _acquire_lock()
        _write_pid()
        asyncio.run(run_async(stop_event, config=cfg))
        return 0
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 1
    finally:
        _clear_pid()
        if lock is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()


def start_background() -> int:
    """Start a background daemon process if one is not already running."""
    if is_running():
        print("hudctl is already running")
        return 0
    ensure_dirs()

    # Double-fork so the daemon is reparented to init and does not zombie.
    first = os.fork()
    if first == 0:  # pragma: no cover
        os.setsid()
        second = os.fork()
        if second == 0:
            with Path(os.devnull).open("r+b", buffering=0) as devnull:
                os.dup2(devnull.fileno(), 0)
                os.dup2(devnull.fileno(), 1)
                os.dup2(devnull.fileno(), 2)
            code = run_foreground()
            os._exit(code)
        os._exit(0)

    os.waitpid(first, 0)
    for _ in range(50):
        if is_running():
            print(f"started hudctl (pid {read_pid()})")
            return 0
        time.sleep(0.05)
    print("timed out waiting for hudctl to start", file=sys.stderr)
    return 1


def stop_daemon(*, timeout: float = 5.0) -> int:
    """Stop the running daemon via SIGTERM, escalating to SIGKILL if needed."""
    pid = read_pid()
    if pid is None or not is_pid_alive(pid):
        _clear_pid()
        print("hudctl is not running")
        return 0
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_pid_alive(pid):
            _clear_pid()
            print(f"stopped hudctl (pid {pid})")
            return 0
        time.sleep(0.05)
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if not is_pid_alive(pid):
            _clear_pid()
            print(f"killed hudctl (pid {pid})")
            return 0
        time.sleep(0.05)
    _clear_pid()
    print(f"timed out waiting for pid {pid} to exit", file=sys.stderr)
    return 1


def reload_daemon() -> int:
    """Ask the running daemon to refresh collectors via SIGHUP."""
    pid = read_pid()
    if pid is None or not is_pid_alive(pid):
        print("hudctl is not running", file=sys.stderr)
        return 1
    os.kill(pid, signal.SIGHUP)
    print(f"sent SIGHUP to hudctl (pid {pid})")
    return 0


def restart_daemon() -> int:
    """Restart the daemon."""
    stop_code = stop_daemon()
    if stop_code != 0:
        return stop_code
    return start_background()


def format_status(*, as_json: bool = False) -> tuple[str, int]:
    """Return (status text, exit code)."""
    running = is_running()
    payload = read_state()
    if as_json:
        body = {
            "running": running,
            "pid": read_pid() if running else None,
            "sections": (payload or {}).get("sections", {}),
            "updated_at": (payload or {}).get("updated_at"),
        }
        return json.dumps(body, indent=2, sort_keys=True), 0 if running else 1

    if not running:
        return "hudctl is not running", 1
    pid = read_pid()
    sections = sorted((payload or {}).get("sections", {}).keys())
    lines = [
        f"hudctl is running (pid {pid})",
        f"sections: {', '.join(sections) if sections else '(none yet)'}",
    ]
    return "\n".join(lines), 0
