"""Install and uninstall user-level huddle integration."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from hudctl.config import (
    config_path,
    default_config,
    ensure_dirs,
    load_config,
    save_config,
)

BEGIN_MARKER = "# huddle begin"
END_MARKER = "# huddle end"

BASH_SNIPPET = """# huddle begin
# Managed by hudctl. Do not edit this block manually.
if command -v hudctl >/dev/null 2>&1; then
  _HUDCTL_LINE="$(hudctl status --json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"sections\",{}).get(\"cwd\",{}).get(\"display\",\"\"))' 2>/dev/null || true)"
fi
# huddle end
"""


@dataclass(frozen=True, slots=True)
class InstallReport:
    """Summary of install/uninstall actions."""

    actions: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def resolve_exec_start() -> str:
    """Return the ExecStart command for the user systemd unit."""
    hudctl = shutil.which("hudctl")
    if hudctl:
        return f"{hudctl} run"
    return f"{sys.executable} -m hudctl run"


def render_unit(*, exec_start: str | None = None) -> str:
    """Render the packaged systemd user unit template."""
    template = (
        resources.files("hudctl.systemd")
        .joinpath("huddle.service")
        .read_text(encoding="utf-8")
    )
    return template.format(exec_start=exec_start or resolve_exec_start())


def systemd_user_dir() -> Path:
    """Return ~/.config/systemd/user."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "systemd" / "user"


def unit_path() -> Path:
    """Return the installed huddle.service path."""
    return systemd_user_dir() / "huddle.service"


def bashrc_path() -> Path:
    """Return the user bashrc path."""
    return Path.home() / ".bashrc"


def _backup_file(path: Path) -> Path | None:
    if not path.is_file():
        return None
    backup = path.with_suffix(path.suffix + ".huddle.bak")
    if not backup.exists():
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return backup
    return backup


def _replace_marked_block(text: str, block: str) -> tuple[str, bool]:
    """Insert or replace a marked block. Returns (new_text, changed)."""
    begin = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if begin != -1 and end != -1 and end > begin:
        end_line = end + len(END_MARKER)
        # Include trailing newline after end marker if present.
        if end_line < len(text) and text[end_line] == "\n":
            end_line += 1
        existing = text[begin:end_line]
        if existing == block or existing.rstrip("\n") == block.rstrip("\n"):
            return text, False
        new_text = text[:begin] + block.rstrip("\n") + "\n" + text[end_line:]
        return new_text, True
    if BEGIN_MARKER in text or END_MARKER in text:
        # Partial/corrupt markers: append a fresh block rather than guessing.
        suffix = "" if text.endswith("\n") or not text else "\n"
        return text + suffix + block.rstrip("\n") + "\n", True
    suffix = "" if text.endswith("\n") or not text else "\n"
    return text + suffix + block.rstrip("\n") + "\n", True


def _remove_marked_block(text: str) -> tuple[str, bool]:
    begin = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        return text, False
    end_line = end + len(END_MARKER)
    if end_line < len(text) and text[end_line] == "\n":
        end_line += 1
    new_text = text[:begin] + text[end_line:]
    return new_text, True


def install_bash_snippet(*, path: Path | None = None) -> str:
    """Install or refresh the bashrc marked block. Returns action description."""
    target = path if path is not None else bashrc_path()
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    updated, changed = _replace_marked_block(existing, BASH_SNIPPET)
    if not changed:
        return f"bash snippet unchanged: {target}"
    _backup_file(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(updated, encoding="utf-8")
    return f"bash snippet updated: {target}"


def uninstall_bash_snippet(*, path: Path | None = None) -> str:
    """Remove the bashrc marked block if present."""
    target = path if path is not None else bashrc_path()
    if not target.is_file():
        return f"bash snippet absent: {target}"
    existing = target.read_text(encoding="utf-8")
    updated, changed = _remove_marked_block(existing)
    if not changed:
        return f"bash snippet absent: {target}"
    _backup_file(target)
    target.write_text(updated, encoding="utf-8")
    return f"bash snippet removed: {target}"


def install_systemd_unit(*, path: Path | None = None) -> str:
    """Write the user systemd unit."""
    target = path if path is not None else unit_path()
    content = render_unit()
    if target.is_file() and target.read_text(encoding="utf-8") == content:
        return f"systemd unit unchanged: {target}"
    _backup_file(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"systemd unit written: {target}"


def uninstall_systemd_unit(*, path: Path | None = None) -> str:
    """Remove the user systemd unit if present."""
    target = path if path is not None else unit_path()
    if not target.is_file():
        return f"systemd unit absent: {target}"
    _backup_file(target)
    target.unlink()
    return f"systemd unit removed: {target}"


def install(*, bashrc: Path | None = None, unit: Path | None = None) -> InstallReport:
    """Install dirs, default config, systemd unit, and bash snippet."""
    actions: list[str] = []
    warnings: list[str] = []

    ensure_dirs()
    actions.append("ensured config/cache/state directories")

    cfg_path = config_path()
    if not cfg_path.is_file():
        save_config(default_config())
        actions.append(f"wrote default config: {cfg_path}")
    else:
        # Validate existing config loads.
        load_config()
        actions.append(f"config present: {cfg_path}")

    actions.append(install_systemd_unit(path=unit))

    if shutil.which("bash") or (bashrc is not None):
        actions.append(install_bash_snippet(path=bashrc))
    else:
        warnings.append("bash not found on PATH; skipped bashrc snippet")

    if not shutil.which("systemctl"):
        warnings.append("systemctl not found; unit written but not enabled")

    return InstallReport(actions=tuple(actions), warnings=tuple(warnings))


def uninstall(
    *,
    bashrc: Path | None = None,
    unit: Path | None = None,
) -> InstallReport:
    """Remove managed systemd unit and bash markers; keep user config."""
    actions = [
        uninstall_systemd_unit(path=unit),
        uninstall_bash_snippet(path=bashrc),
    ]
    return InstallReport(
        actions=tuple(actions),
        warnings=("user config/cache/state left in place",),
    )


def format_install_report(report: InstallReport, *, verb: str) -> str:
    """Format an install/uninstall report for the CLI."""
    lines = [f"hudctl {verb}"]
    lines.extend(f"  - {action}" for action in report.actions)
    for warning in report.warnings:
        lines.append(f"  ! {warning}")
    return "\n".join(lines)
