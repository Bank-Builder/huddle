"""Environment diagnostics for hudctl doctor."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from hudctl import __version__
from hudctl.config import cache_dir, config_dir, ensure_dirs, state_dir

WhichFn = Callable[[str], str | None]


class CheckStatus(Enum):
    """Outcome of a single doctor check."""

    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Result of one diagnostic check."""

    name: str
    status: CheckStatus
    detail: str


def _check_python(*, version_info: tuple[int, ...] | None = None) -> CheckResult:
    info = version_info if version_info is not None else sys.version_info[:2]
    major, minor = info[0], info[1]
    version = f"{major}.{minor}"
    if (major, minor) >= (3, 12):
        return CheckResult("python", CheckStatus.OK, f"Python {version}")
    return CheckResult(
        "python",
        CheckStatus.FAIL,
        f"Python {version} is below required 3.12",
    )


def _check_linux(*, platform: str = sys.platform) -> CheckResult:
    if platform.startswith("linux"):
        return CheckResult("linux", CheckStatus.OK, platform)
    return CheckResult(
        "linux",
        CheckStatus.FAIL,
        f"unsupported platform: {platform}",
    )


def _check_path_writable(name: str, path: Path) -> CheckResult:
    try:
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
        probe = path / ".hudctl-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        return CheckResult(name, CheckStatus.FAIL, f"{path}: {exc}")
    return CheckResult(name, CheckStatus.OK, str(path))


def _check_binary(
    name: str,
    binary: str,
    which: WhichFn,
    *,
    required: bool = False,
) -> CheckResult:
    located = which(binary)
    if located:
        return CheckResult(name, CheckStatus.OK, located)
    status = CheckStatus.FAIL if required else CheckStatus.WARN
    return CheckResult(name, status, f"{binary} not found on PATH")


def run_checks(
    *,
    which: WhichFn = shutil.which,
    platform: str = sys.platform,
    version_info: tuple[int, ...] | None = None,
) -> list[CheckResult]:
    """Run doctor checks and return ordered results."""
    ensure_dirs()
    return [
        CheckResult("hudctl", CheckStatus.OK, f"version {__version__}"),
        _check_python(version_info=version_info),
        _check_linux(platform=platform),
        CheckResult(
            "path",
            CheckStatus.OK if os.environ.get("PATH") else CheckStatus.FAIL,
            os.environ.get("PATH") or "PATH is empty",
        ),
        _check_path_writable("config-dir", config_dir()),
        _check_path_writable("cache-dir", cache_dir()),
        _check_path_writable("state-dir", state_dir()),
        _check_binary("kitty", "kitty", which),
        _check_binary("bash", "bash", which),
        _check_binary("zsh", "zsh", which),
        _check_binary("fish", "fish", which),
        _check_binary("systemd-user", "systemctl", which),
    ]


def summarize(results: Sequence[CheckResult]) -> CheckStatus:
    """Return the worst status among results."""
    if any(result.status is CheckStatus.FAIL for result in results):
        return CheckStatus.FAIL
    if any(result.status is CheckStatus.WARN for result in results):
        return CheckStatus.WARN
    return CheckStatus.OK


def format_report(results: Sequence[CheckResult]) -> str:
    """Format doctor results as plain text."""
    lines = ["hudctl doctor"]
    for result in results:
        lines.append(f"[{result.status.value}] {result.name}: {result.detail}")
    overall = summarize(results)
    lines.append(f"overall: {overall.value}")
    return "\n".join(lines)


def doctor_exit_code(results: Sequence[CheckResult]) -> int:
    """Exit non-zero only on hard failures."""
    return 1 if summarize(results) is CheckStatus.FAIL else 0
