"""Tests for hudctl doctor diagnostics."""

from __future__ import annotations

from pathlib import Path

import pytest

from hudctl.cli.doctor import (
    CheckResult,
    CheckStatus,
    doctor_exit_code,
    format_report,
    run_checks,
    summarize,
)
from hudctl.cli.main import main


@pytest.fixture
def xdg_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    return tmp_path


def test_summarize_and_exit_code() -> None:
    ok = [CheckResult("a", CheckStatus.OK, "fine")]
    warn = [CheckResult("a", CheckStatus.WARN, "missing")]
    fail = [CheckResult("a", CheckStatus.FAIL, "broken")]
    assert summarize(ok) is CheckStatus.OK
    assert summarize(warn) is CheckStatus.WARN
    assert summarize(fail) is CheckStatus.FAIL
    assert doctor_exit_code(ok) == 0
    assert doctor_exit_code(warn) == 0
    assert doctor_exit_code(fail) == 1


def test_format_report_includes_overall() -> None:
    report = format_report([CheckResult("python", CheckStatus.OK, "Python 3.12")])
    assert "hudctl doctor" in report
    assert "[ok] python: Python 3.12" in report
    assert "overall: ok" in report


def test_run_checks_with_fake_which(xdg_home: Path) -> None:
    _ = xdg_home

    def fake_which(name: str) -> str | None:
        mapping = {
            "bash": "/bin/bash",
            "systemctl": "/usr/bin/systemctl",
        }
        return mapping.get(name)

    results = run_checks(which=fake_which)
    by_name = {result.name: result for result in results}
    assert by_name["bash"].status is CheckStatus.OK
    assert by_name["kitty"].status is CheckStatus.WARN
    assert by_name["config-dir"].status is CheckStatus.OK
    assert doctor_exit_code(results) == 0


def test_run_checks_fails_on_non_linux(xdg_home: Path) -> None:
    _ = xdg_home
    results = run_checks(platform="darwin", which=lambda _name: None)
    by_name = {result.name: result for result in results}
    assert by_name["linux"].status is CheckStatus.FAIL
    assert doctor_exit_code(results) == 1


def test_run_checks_fails_on_old_python(xdg_home: Path) -> None:
    _ = xdg_home
    results = run_checks(version_info=(3, 11, 0), which=lambda _name: "/bin/true")
    by_name = {result.name: result for result in results}
    assert by_name["python"].status is CheckStatus.FAIL
    assert doctor_exit_code(results) == 1


def test_cli_doctor_succeeds(
    xdg_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = xdg_home
    code = main(["doctor"])
    out = capsys.readouterr().out
    assert "hudctl doctor" in out
    assert "overall:" in out
    assert code in {0, 1}
