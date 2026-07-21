"""hudctl console entry point."""

from __future__ import annotations

import argparse
import sys

from hudctl import __version__
from hudctl.cli.doctor import doctor_exit_code, format_report, run_checks
from hudctl.daemon import (
    format_status,
    restart_daemon,
    run_foreground,
    start_background,
    stop_daemon,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="hudctl",
        description="Huddle terminal context engine",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("version", help="Print package version")
    subparsers.add_parser("doctor", help="Diagnose environment and paths")
    subparsers.add_parser("start", help="Start the background daemon")
    subparsers.add_parser("stop", help="Stop the background daemon")
    subparsers.add_parser("restart", help="Restart the background daemon")
    status = subparsers.add_parser("status", help="Show daemon status")
    status.add_argument(
        "--json",
        action="store_true",
        help="Emit status as JSON",
    )
    subparsers.add_parser("run", help="Run the daemon in the foreground")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the hudctl CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        results = run_checks()
        print(format_report(results))
        return doctor_exit_code(results)

    if args.command == "start":
        return start_background()

    if args.command == "stop":
        return stop_daemon()

    if args.command == "restart":
        return restart_daemon()

    if args.command == "status":
        text, code = format_status(as_json=bool(args.json))
        print(text)
        return code

    if args.command == "run":
        return run_foreground()

    print(__version__)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
