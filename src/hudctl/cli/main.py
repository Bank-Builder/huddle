"""hudctl console entry point."""

from __future__ import annotations

import argparse
import sys

from hudctl import __version__
from hudctl.cli.doctor import doctor_exit_code, format_report, run_checks


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="hudctl",
        description="Huddle terminal context engine",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("version", help="Print package version")
    subparsers.add_parser("doctor", help="Diagnose environment and paths")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the hudctl CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        results = run_checks()
        print(format_report(results))
        return doctor_exit_code(results)

    print(__version__)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
