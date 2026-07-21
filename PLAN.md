# PLAN.md

# Huddle / hudctl

**Tagline**

> A unified terminal context engine with pluggable renderers.

**PyPI distribution name:** `hudctl` (available; verified 2026-07-21)

**Product name:** Huddle

**CLI / installable package:** `hudctl`

```bash
# end users (any installer)
pip install hudctl
# or
uv tool install hudctl

hudctl start
```

---

# Vision

Huddle is a lightweight daemon that continuously gathers developer context (Git, current directory, Docker, Kubernetes, network throughput, CPU, memory, SSH, battery, time, etc.) and exposes it through multiple renderers.

Unlike traditional shell prompts that repeatedly execute expensive commands every time the prompt is displayed, Huddle collects information once, caches it intelligently, and allows multiple consumers to share the same data.

The architecture separates:

* Collection
* State
* Rendering

This makes the project extensible, efficient and terminal-agnostic.

The first renderer will target Kitty, but the architecture must support Bash, Zsh, Fish, tmux, JSON output and future IDE integrations.

---

# PyPI Name Decision

| Candidate        | PyPI status | Notes                                      |
| ---------------- | ----------- | ------------------------------------------ |
| `huddle`         | **TAKEN**   | Unrelated auto-deployment tool (v0.1.5)    |
| `pyhuddle`       | **TAKEN**   | Occupied                                   |
| `hudctl`         | **AVAILABLE** | Chosen: matches CLI, clear, short        |
| `huddle-term`    | Available   | Fallback if needed                         |
| `huddle-ctx`     | Available   | Fallback if needed                         |
| `huddle-engine`  | Available   | Fallback if needed                         |

**Decision:** Ship as **`hudctl`** on PyPI.

* Distribution name: `hudctl`
* Import package: `hudctl`
* Console script: `hudctl`
* Config/cache dirs retain product branding: `~/.config/huddle/`, `~/.cache/huddle/`
* systemd unit: `huddle.service` (user unit)

This avoids clashing with the existing `huddle` PyPI project while keeping familiar path names.

---

# Design Principles

* Linux first
* Python 3.12+
* Zero mandatory runtime dependencies outside the Python standard library
* Optional extras for optional features only (never required for core)
* No shell framework required
* No tmux required
* No root privileges required
* User-level installation via `pip install hudctl` or `uv tool install hudctl`
* **Development and release tooling: uv** (venv, sync, lock, run, build, publish)
* User-level systemd service
* Very low CPU usage (<1%)
* Very low memory usage (<20MB)
* Plugin architecture from day one
* Strong typing
* Extensive unit tests
* Clear documentation
* High code quality
* PyPI-publishable from the first tagged release

---

# Core Concepts

Huddle consists of four independent layers.

```
Collectors
    ↓
Context Engine
    ↓
Renderer
    ↓
Output
```

Collectors gather information.

The engine owns state, scheduling and caching.

Renderers transform state into terminal-specific output.

Outputs send that rendered information to Kitty, Bash, tmux, JSON or future consumers.

No renderer may directly gather system information.

No collector may know anything about rendering.

---

# Repository Structure (src layout, PyPI-ready)

Use a **src layout** so packaging and editable installs behave correctly.

```
huddle/                          # git repository root
    README.md
    LICENSE                      # MIT (present)
    CHANGELOG.md
    CONTRIBUTING.md
    PLAN.md
    SECURITY.md
    pyproject.toml               # sole packaging config
    uv.lock                      # committed; reproducible deps
    .python-version              # pinned via uv (3.12+)
    Makefile                     # wraps uv run / uv build
    .gitignore
    .github/
        workflows/
            ci.yml               # lint, typecheck, test, coverage
            release.yml          # build + publish to PyPI on tag
    docs/
        architecture.md
        plugin-api.md
        installation.md
        themes.md
        packaging.md
        faq.md
        troubleshooting.md
        screenshots/
    src/
        hudctl/
            __init__.py          # __version__
            py.typed             # PEP 561 marker
            engine.py
            scheduler.py
            cache.py
            state.py
            config.py
            daemon.py
            formatter.py
            events.py
            utils.py
            collectors/
                __init__.py
                base.py
                cwd.py
                git.py
                network.py
                cpu.py
                memory.py
                clock.py
                ssh.py
                hostname.py
                docker.py
                kubernetes.py
                battery.py
                vpn.py
            renderers/
                __init__.py
                base.py
                kitty.py
                bash.py
                zsh.py
                fish.py
                tmux.py
                json.py
            themes/
                minimal.toml
                developer.toml
                compact.toml
                powerline.toml
            cli/
                __init__.py
                main.py          # entry point for console_scripts
                doctor.py
                install.py
                uninstall.py
            systemd/
                huddle.service   # packaged unit template
    tests/
        unit/
        integration/
        conftest.py
    examples/
        config.toml
        custom_collector/
```

Removed: top-level `installer/` and `cli/` as separate trees. Install/doctor live under `hudctl.cli` and are invoked via `hudctl` subcommands after install.

**Dev toolchain:** [uv](https://docs.astral.sh/uv/) is mandatory for contributors and CI. Do not use bare `pip`/`venv`/`python -m build`/`twine` in project docs or Makefile targets.

---

# Packaging Specification (deployable PyPI app)

## pyproject.toml requirements

```toml
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "hudctl"
version = "0.1.0"
description = "Unified terminal context engine with pluggable renderers"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.12"
authors = [
  { name = "bank-builder" }
]
keywords = [
  "terminal", "prompt", "kitty", "bash", "zsh", "context", "daemon"
]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Operating System :: POSIX :: Linux",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: System :: Shells",
  "Typing :: Typed",
]
dependencies = []   # stdlib only for core

[dependency-groups]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "ruff>=0.6",
  "mypy>=1.11",
]

# Prefer uv dependency-groups over optional-dependencies for dev tools.
# End-user runtime deps stay empty (stdlib only).

[tool.uv]
package = true

[project.scripts]
hudctl = "hudctl.cli.main:main"

[project.entry-points."hudctl.collectors"]
# third-party collectors register here

[project.entry-points."hudctl.renderers"]
# third-party renderers register here

[project.urls]
Homepage = "https://github.com/bank-builder/huddle"
Documentation = "https://github.com/bank-builder/huddle#readme"
Repository = "https://github.com/bank-builder/huddle"
Issues = "https://github.com/bank-builder/huddle/issues"
Changelog = "https://github.com/bank-builder/huddle/blob/main/CHANGELOG.md"

[tool.hatch.build.targets.wheel]
packages = ["src/hudctl"]

[tool.hatch.build.targets.sdist]
include = [
  "src/hudctl",
  "tests",
  "docs",
  "examples",
  "LICENSE",
  "README.md",
  "CHANGELOG.md",
  "pyproject.toml",
]
```

## Distribution artefacts

| Artefact                         | Purpose                          |
| -------------------------------- | -------------------------------- |
| `hudctl-<ver>-py3-none-any.whl`  | Wheel (pure Python, Linux-first) |
| `hudctl-<ver>.tar.gz`            | Source distribution              |

Wheel is `py3-none-any` because the code is pure Python; Linux-specific behaviour is runtime, not binary.

## Install paths after `pip install hudctl` / `uv tool install hudctl`
| What              | Where                                              |
| ----------------- | -------------------------------------------------- |
| Package           | site-packages/`hudctl/`                            |
| CLI               | PATH/`hudctl`                                      |
| User config       | `~/.config/huddle/config.toml`                     |
| Cache             | `~/.cache/huddle/`                                 |
| Runtime state     | `~/.local/state/huddle/` (socket, pid)             |
| systemd unit      | `~/.config/systemd/user/huddle.service` (installed by `hudctl install`) |

## Versioning

* SemVer: `MAJOR.MINOR.PATCH`
* Single source of truth: `project.version` in `pyproject.toml`
* Bump with `uv version` (or edit `pyproject.toml`, then `uv lock`)
* Expose as `hudctl.__version__` (read from package metadata at runtime via `importlib.metadata`)
* Git tags: `v0.1.0`, `v0.2.0`, ...
* PyPI publish only from annotated tags via CI

## Release checklist (every publish)

1. Tests green on CI (3.12, 3.13) via `uv sync --group dev` + `make check`
2. `uv run ruff check`, `uv run mypy`, coverage gate met
3. CHANGELOG.md updated
4. Version bumped (`uv version X.Y.Z` or edit + `uv lock`)
5. Tag `vX.Y.Z`
6. CI runs `uv build --no-sources` then `uv publish` (Trusted Publishing / OIDC)
7. Verify: `uv tool install hudctl==X.Y.Z` (or `pip install`) and `hudctl version`

## Local package smoke test (mandatory before first publish)

```bash
uv build --no-sources
uv venv /tmp/hudctl-smoke
uv pip install --python /tmp/hudctl-smoke dist/hudctl-*.whl
/tmp/hudctl-smoke/bin/hudctl version
/tmp/hudctl-smoke/bin/hudctl doctor
```

---

# Project Architecture

```
                    +-------------------+
                    |   Collectors      |
                    +-------------------+

               Git / CPU / RAM / Network
               Docker / Kubernetes / SSH
               Clock / Battery / VPN

                         │
                         ▼
                 Context Engine
          scheduling / caching
          event dispatch / plugins
                         │
                         ▼
                   Formatter
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Kitty          Bash Prompt      JSON
```

---

# Collector Interface

Every collector must implement exactly the same interface.

```python
from abc import ABC, abstractmethod
from typing import Any


class Collector(ABC):
    name: str
    interval: float  # seconds

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Return structured data for this collector's state section."""
```

Collectors must never print.

Collectors must never format strings.

Collectors return structured data only.

Example:

```python
{
    "branch": "main",
    "dirty": True
}
```

---

# Scheduling

Collectors run independently. No collector may block another.

| Collector  | Interval   |
| ---------- | ---------- |
| Clock      | 1 second   |
| Network    | 1 second   |
| CPU        | 2 seconds  |
| Memory     | 2 seconds  |
| Git        | 5 seconds  |
| Kubernetes | 20 seconds |
| Docker     | 30 seconds |
| VPN        | 30 seconds |
| Battery    | 60 seconds |

Use `asyncio` (stdlib) or a lightweight thread+timer scheduler. Prefer asyncio for I/O-bound collectors; keep CPU work short and non-blocking.

---

# State

The engine owns one immutable (or copy-on-write) state object.

```python
{
    "cwd": "...",
    "git": {...},
    "cpu": {...},
    "memory": {...},
    "network": {...},
    "docker": {...},
    "clock": {...}
}
```

Collectors update only their section. Renderers receive a snapshot.

IPC: daemon writes state to a Unix domain socket and/or a small state file under `~/.local/state/huddle/` so `hudctl status` works without attaching to the process.

---

# Renderers

Renderers consume state.

They never execute shell commands.

They never read `/proc`.

They never invoke Git.

Renderers are pure functions:

```python
def render(state: Mapping[str, Any], theme: Theme) -> str:
    ...
```

---

# Theme Engine

Themes define separators, icons, colours, abbreviations, formatting rules.

Theme files are TOML, shipped in the package and overridable from `~/.config/huddle/themes/`.

---

# Kitty Renderer

Uses Kitty Remote Control API.

Updates window title and tab title.

Fallback to ANSI escape sequences if Remote Control is unavailable.

---

# Bash Renderer

Generates PS1 fragments.

Supports one-line and two-line prompts.

Must be installable without overwriting existing user configuration (append sourced snippet with markers).

---

# JSON Renderer

```
hudctl status --json
```

Outputs current state for scripts and IDE integrations.

---

# CLI

Single console script installed by the wheel:

```
hudctl
```

Commands:

```
hudctl start
hudctl stop
hudctl restart
hudctl status
hudctl status --json
hudctl doctor
hudctl install
hudctl uninstall
hudctl reload
hudctl plugins
hudctl theme list
hudctl theme set developer
hudctl config edit
hudctl version
```

---

# Configuration

User configuration:

```
~/.config/huddle/config.toml
```

Example:

```toml
theme = "developer"
refresh = 1

renderers = [
    "kitty",
    "bash"
]

modules = [
    "cwd",
    "git",
    "cpu",
    "memory",
    "network",
    "clock"
]
```

---

# Installation (user-facing)

Primary path (PyPI):

```bash
pip install --user hudctl
# or (recommended for CLI tools)
uv tool install hudctl

hudctl install
hudctl start
```

`hudctl install` must:

* detect Kitty / Bash / Zsh / Fish
* create configuration, cache, and state directories
* install user systemd unit from packaged template
* enable linger-friendly user service where appropriate
* install shell integration snippets with backup markers
* never duplicate configuration
* be idempotent and reversible via `hudctl uninstall`

Secondary path: contributor development with **uv** (required):

```bash
uv python pin 3.12
uv sync --group dev
uv run hudctl version
```

---

# Cache and runtime

```
~/.cache/huddle/           # persistent cache for slow collectors
~/.local/state/huddle/     # pid, socket, last snapshot
```

---

# Performance Targets

| Metric            | Target                          |
| ----------------- | ------------------------------- |
| Startup           | <100 ms                         |
| Memory            | <20 MB RSS                      |
| CPU               | <1% idle steady state           |
| Network collector | No subprocesses                 |
| Git collector     | Cache; avoid repeated expensive invocations |

---

# Plugin System

Third-party plugins installable without modifying core.

Discovery via:

1. Python entry points: `hudctl.collectors`, `hudctl.renderers`
2. Optional user plugin directory: `~/.config/huddle/plugins/`

Plugin API stable after v1.0.

---

# Testing

* pytest + pytest-cov
* Target: **>90% coverage** (CI fail below gate)
* Unit tests for collectors (mocked `/proc`, git), engine, renderers, CLI
* Integration tests for daemon start/stop/status (no root)
* Packaging tests: import, entry point, version metadata
* No tests requiring root
* Prefer factories/fixtures over ad-hoc setup; mock external services

---

# Coding Standards

Aligned with normal Python project practices for this workspace:

| Practice | Tool / rule |
| -------- | ----------- |
| Lint | **Ruff** (`ruff check`) |
| Format | **Ruff format** (Black-compatible; do **not** also run Black) |
| Import sort | **Ruff** (`I` rules; replaces isort) |
| Types | **mypy --strict** on `src/hudctl`; public APIs pyright-compatible |
| Tests | **pytest** + **pytest-cov** |
| Line length | **88** (Black / Ruff default) |
| Style | PEP 8 via Ruff; type hints on all function signatures |
| Docs | Docstrings on all public modules, classes, functions |
| Env | **uv**-managed `.venv/` (never commit); pin via `.python-version` |
| Deps | `pyproject.toml` + committed **`uv.lock`** (no `requirements.txt`) |
| Project mgr | **uv** (`sync`, `run`, `lock`, `build`, `publish`, `tool`) |
| Logging | stdlib `logging` only |
| Paths | `pathlib` |
| Data | `dataclasses` (or attrs-free stdlib) |
| State | Avoid global mutable state |
| Typing package | Ship `py.typed` (PEP 561) |

**Do not add:** Black (redundant with Ruff format), isort (redundant with Ruff `I`), flake8 (redundant with Ruff), Poetry, pip-tools, or bare `venv`/`pip install -e` workflows for this repo.

**Do not use in Makefile/CI/docs for this project:** `python -m build`, `twine`, `python -m venv`, `pip install -e`.

---

# Python Quality Tooling (locked config)

All tool config lives in `pyproject.toml`. Phase 0 must include these sections.

**Package/project manager: uv** (required for all development, CI, build, and publish).

## uv project setup

```bash
# one-time / Phase 0
uv python pin 3.12
uv sync --group dev          # creates .venv, writes uv.lock
uv lock                      # refresh lock after dep changes
uv run <cmd>                 # run tools inside the project env
uv build --no-sources        # sdist + wheel into dist/
uv publish                   # upload to PyPI (CI / trusted publishing)
uv tool install hudctl       # end-user CLI install (alternative to pip)
uv version X.Y.Z             # bump project version
```

Commit **`uv.lock`** and **`.python-version`**. Ignore `.venv/`.

CI should use the official `astral-sh/setup-uv` action and cache.

## Ruff

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
  "E",     # pycodestyle errors
  "W",     # pycodestyle warnings
  "F",     # pyflakes
  "I",     # isort
  "B",     # flake8-bugbear
  "UP",    # pyupgrade
  "SIM",   # flake8-simplify
  "RUF",   # ruff-specific
  "N",     # pep8-naming
  "ASYNC", # flake8-async
  "S",     # flake8-bandit (security); tests may ignore S101
  "T20",   # flake8-print (no print in library code)
  "C4",    # flake8-comprehensions
  "PT",    # flake8-pytest-style
]
ignore = [
  "E501",  # line length handled by formatter
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # assert allowed in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

## mypy

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
warn_return_any = true
show_error_codes = true
pretty = true
files = ["src/hudctl"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

## pytest / coverage

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = [
  "-ra",
  "--strict-markers",
  "--strict-config",
]
filterwarnings = ["error"]

[tool.coverage.run]
branch = true
source = ["hudctl"]

[tool.coverage.report]
fail_under = 90
show_missing = true
skip_covered = false
exclude_lines = [
  "pragma: no cover",
  "if TYPE_CHECKING:",
  "\\.\\.\\.",
]
```

## Makefile (required, keep simple)

Ship a root `Makefile` that wraps uv. No fancy help text, no smoke target in Make.

```makefile
.PHONY: sync lint fmt check test typecheck build

sync:
	uv sync --group dev

lint:
	uv run ruff check .
	uv run ruff format --check .

fmt:
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck test

build:
	uv build --no-sources
```

CI: `uv sync --group dev` then `make check` on Python 3.12 and 3.13.

## Local developer workflow

```bash
uv python pin 3.12
make sync
make fmt
make check
uv run hudctl version
make build
```

## Optional: pre-commit (Phase 0 or 1)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9  # pin; bump deliberately
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
        additional_dependencies: []
```

pre-commit is recommended but not a substitute for CI `make check`.

---

# Documentation

Produce and keep aligned with code:

* Architecture Guide
* Plugin Development Guide
* Theme Guide
* Installation Guide (uv tool / pip / systemd)
* Packaging Guide (uv build / uv publish / release process)
* FAQ
* Troubleshooting Guide

Every public class and function should have docstrings.

---

# Roadmap (product versions)

## Version 0.1.0 (first PyPI release)

* Engine, scheduler, state, cache
* Collectors: cwd, git, clock, network, cpu, memory
* Renderers: kitty, bash, json (minimal)
* CLI: start/stop/restart/status/doctor/install/uninstall/version
* User systemd unit
* `pyproject.toml`, wheel, sdist
* CI: lint, typecheck, test
* Docs: README + installation

## Version 0.2.0

* Docker, Kubernetes, SSH, hostname collectors
* Stronger git caching

## Version 0.3.0

* Theme engine
* Fish and Zsh renderers
* tmux renderer (optional)

## Version 0.4.0

* Plugin API (entry points)
* Configuration reload
* External plugin example package

## Version 1.0.0

* Stable public APIs
* Complete documentation
* Production-ready installer
* Trusted PyPI publishing
* Comprehensive test suite (>90%)

---

# Detailed Implementation Plan

Work in small commits. Each phase ends with tests green and a working installable tree. Do not generate placeholder stubs that raise `NotImplementedError` as shipped behaviour.

## Phase 0 — Scaffolding and packaging skeleton

**Goal:** Empty but installable `hudctl` package on the local machine, with uv + quality tooling locked in.

**Tasks:**

1. Ensure `uv` is available; pin Python with `uv python pin 3.12`
2. Create `src/hudctl/` with `__init__.py`, `py.typed`, `__version__` via `importlib.metadata`
3. Write complete `pyproject.toml` (hatchling, scripts, classifiers, urls, `[dependency-groups]`, `[tool.uv]`)
4. Embed locked `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]` sections from this PLAN
5. Add minimal `hudctl.cli.main:main` that prints version and exits 0
6. `uv sync --group dev` and commit `uv.lock` + `.python-version`
7. Add simple root `Makefile` (`sync`, `lint`, `fmt`, `typecheck`, `test`, `check`, `build`)
8. Add `tests/unit/test_version.py`
9. Add GitHub Actions `ci.yml` using `astral-sh/setup-uv`, matrix 3.12/3.13, `make sync` + `make check`
10. Optional: `.pre-commit-config.yaml` for Ruff + mypy
11. Update README with `uv tool install hudctl` and `pip install hudctl`

**Exit criteria:**

```bash
make sync
make check
uv run hudctl version
make build
```

**Commit:** `chore: scaffold hudctl package with uv for PyPI`

---

## Phase 1 — Config, paths, and doctor

**Goal:** XDG paths, config load/save, environment diagnostics.

**Tasks:**

1. `hudctl.config` — load/merge defaults + `~/.config/huddle/config.toml` (tomllib)
2. Path helpers: config, cache, state dirs; create with correct permissions
3. `hudctl doctor` — Python version, Linux, PATH, Kitty, shells, systemd --user, write permissions
4. Unit tests with tmp_path fixtures (no real home writes)

**Exit criteria:** `hudctl doctor` exits non-zero only on hard failures; tests cover missing config and defaults.

**Commit:** `feat: add config paths and doctor command`

---

## Phase 2 — State, cache, events

**Goal:** Shared immutable state model and cache layer.

**Tasks:**

1. `state.py` — typed state container; sectional updates; snapshot copy
2. `cache.py` — disk cache under `~/.cache/huddle/` with TTL
3. `events.py` — simple pub/sub for "section updated"
4. Unit tests for merge semantics and cache expiry

**Exit criteria:** Pure unit tests; no daemon yet.

**Commit:** `feat: add state, cache, and event bus`

---

## Phase 3 — Scheduler and engine

**Goal:** Run collectors on intervals without blocking each other.

**Tasks:**

1. `collectors/base.py` — `Collector` ABC
2. `scheduler.py` — asyncio loop; per-collector interval; error isolation (one failure does not stop others)
3. `engine.py` — register collectors, update state, emit events
4. Tests with fake collectors and fake clocks

**Exit criteria:** Engine runs N fake collectors for a few ticks in tests; coverage for error isolation.

**Commit:** `feat: add scheduler and context engine`

---

## Phase 4 — Core collectors (v0.1 set)

**Goal:** Real collectors for cwd, clock, cpu, memory, network, git.

**Tasks (one collector per commit preferred):**

1. `clock.py` — local time; no subprocess
2. `cwd.py` — resolve cwd from env/process; symlink-aware
3. `cpu.py` / `memory.py` — read `/proc`; no subprocess
4. `network.py` — `/proc/net/dev` deltas; no subprocess
5. `git.py` — minimal porcelain or `.git` parsing; aggressive caching; never block engine

**Exit criteria:** Each collector has unit tests with fixtures/mocks; performance notes in docstrings where relevant.

**Commits:** `feat: add <name> collector` (per module)

---

## Phase 5 — Daemon and IPC

**Goal:** Long-running process with start/stop/status.

**Tasks:**

1. `daemon.py` — PID file, Unix socket or state file, graceful SIGTERM
2. CLI: `start`, `stop`, `restart`, `status`, `status --json`
3. Ensure single-instance lock
4. Integration tests: start, status, stop (tmpdir, no systemd required)

**Exit criteria:** `hudctl start` then `hudctl status --json` returns collector sections.

**Commit:** `feat: add daemon lifecycle and status IPC`

---

## Phase 6 — Formatter and first renderers

**Goal:** Pure render path from state to strings.

**Tasks:**

1. `formatter.py` — apply theme tokens to sections
2. Ship `themes/minimal.toml` and `themes/developer.toml`
3. `renderers/json.py` — dump state
4. `renderers/bash.py` — PS1 fragment generation
5. `renderers/kitty.py` — remote control + ANSI fallback
6. Unit tests: golden-string snapshots for bash/json

**Exit criteria:** Renderers never call collectors; tests prove purity with injected state.

**Commit:** `feat: add formatter and kitty/bash/json renderers`

---

## Phase 7 — Install / uninstall / systemd

**Goal:** Idempotent user install that is reversible.

**Tasks:**

1. Package `systemd/huddle.service` template with `%h` / `ExecStart=hudctl` paths resolved at install time
2. `hudctl install` — dirs, config, unit, shell snippet with `# huddle begin/end` markers, backups
3. `hudctl uninstall` — remove only managed markers/files; leave user data optional flag
4. Tests for marker insertion/removal and unit template rendering

**Exit criteria:** Install twice does not duplicate snippets; uninstall restores prior state for managed sections.

**Commit:** `feat: add install/uninstall and user systemd unit`

---

## Phase 8 — Reload, themes CLI, polish

**Goal:** Operator UX for day-to-day use.

**Tasks:**

1. `hudctl reload` — SIGHUP or control socket message
2. `hudctl theme list` / `theme set`
3. `hudctl config edit` — `$EDITOR` on config path
4. Logging levels via config/env
5. README screenshots/docs stubs for architecture and installation

**Exit criteria:** Manual smoke on a Linux box: install, start, status, theme set, reload, uninstall.

**Commit:** `feat: add reload and theme CLI commands`

---

## Phase 9 — CI release pipeline and first PyPI publish

**Goal:** Tagged releases publish `hudctl` to PyPI automatically via uv.

**Tasks:**

1. `.github/workflows/release.yml` — on `v*` tag: `uv build --no-sources`, then `uv publish` (Trusted Publishing / OIDC)
2. Prefer PyPI Trusted Publishing over long-lived tokens (`UV_PUBLISH_TOKEN` only as fallback)
3. Test publish to TestPyPI once before first production publish (`uv publish --index testpypi` or equivalent)
4. CHANGELOG.md for 0.1.0
5. Smoke install from TestPyPI: `uv tool install --index-url https://test.pypi.org/simple/ hudctl`

**Exit criteria:**

```bash
uv tool install hudctl==0.1.0
hudctl version
```

**Commit:** `ci: add uv-based PyPI release workflow` then tag `v0.1.0`

---

## Phase 10+ — Roadmap alignment

Follow product roadmap 0.2 → 1.0:

* 0.2 collectors (docker, k8s, ssh, hostname)
* 0.3 themes + fish/zsh/tmux
* 0.4 entry-point plugins + example plugin package on PyPI (e.g. `hudctl-plugin-example`)
* 1.0 API freeze, docs complete, coverage gate

Each minor version is a PyPI release with CHANGELOG entry.

---

# Implementation Rules for Cursor

1. Implement incrementally. Each commit leaves the project installable and testable.
2. Do not ship placeholder code as product behaviour.
3. Write tests for new functionality before considering a task complete.
4. Prefer composition over inheritance.
5. Keep collectors, engine, renderers, and CLI strictly decoupled.
6. Design public APIs carefully to minimise breaking changes before 1.0.
7. Treat performance as a first-class requirement.
8. **Always** validate packaging when touching `pyproject.toml` or entry points:
   `uv build --no-sources` (and smoke-install the wheel)
9. Never use the distribution name `huddle` on PyPI; the published name is **`hudctl`**.
10. Modify one module/segment at a time; commit frequently between phases; push only when instructed.
11. Before considering any phase done, run `make check` (via uv: Ruff lint + format check + mypy + pytest/cov).
12. Do not introduce Black, isort, or flake8 alongside Ruff.
13. Use **uv** for all project env, lock, run, build, and publish steps. Do not document or script `pip install -e`, `python -m venv`, `python -m build`, or `twine` for this repository.
14. Keep `uv.lock` committed and in sync after dependency or version changes (`uv lock` / `uv sync --group dev`).

---

# Immediate Next Step

Execute **Phase 0** only: scaffold `src/hudctl`, `pyproject.toml`, `uv sync --group dev`, version CLI, tests, and `uv build` smoke. Stop and confirm before Phase 1.
