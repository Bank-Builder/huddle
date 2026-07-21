# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Release workflow that builds on `v*` tags and uploads artifacts
- Manual workflow_dispatch PyPI publish gate (disabled by default)

## [0.1.0] - 2026-07-21

### Added

- `hudctl` package scaffold with uv, Ruff, mypy, and pytest
- Context engine, scheduler, state, cache, and event bus
- Collectors: clock, cwd, cpu, memory, network, git
- Daemon lifecycle: start, stop, restart, reload, status, run
- Renderers: json, bash, kitty (pure state consumers)
- Themes: minimal, developer
- Install/uninstall with user systemd unit and bashrc markers
- Theme list/set, config edit, doctor

[Unreleased]: https://github.com/Bank-Builder/huddle/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Bank-Builder/huddle/releases/tag/v0.1.0
