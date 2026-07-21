"""hudctl console entry point."""

from __future__ import annotations

import argparse
import sys

from hudctl import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="hudctl",
        description="Huddle terminal context engine",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("version", help="Print package version")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the hudctl CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Default and explicit version both print the package version.
    _ = args.command
    print(__version__)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
