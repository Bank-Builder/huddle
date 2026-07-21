# Huddle / hudctl

Unified terminal context engine with pluggable renderers.

`hudctl` runs a user-level daemon that collects developer context once
(Git, cwd, CPU, memory, network, clock) and exposes it to status/JSON
consumers and future prompt/title integrations.

**PyPI name:** `hudctl` (not `huddle`). Not published to PyPI yet; use a
local checkout or a locally built wheel.

## Quick start (from this repo)

```bash
uv python pin 3.12
make sync
uv run hudctl doctor
uv run hudctl install
uv run hudctl start
uv run hudctl status
uv run hudctl status --json
```

`make` with no arguments prints available targets.

## Install paths

After `hudctl install`:

| Item | Location |
|------|----------|
| Config | `~/.config/huddle/config.toml` |
| Cache | `~/.cache/huddle/` |
| State / PID | `~/.local/state/huddle/` |
| systemd unit | `~/.config/systemd/user/huddle.service` |
| bash hook | marked block in `~/.bashrc` (`# huddle begin` / `# huddle end`) |

Optional user service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now huddle.service
```

`hudctl uninstall` removes the managed unit and bash markers; it keeps
config/cache/state.

## CLI reference

```bash
hudctl version
hudctl doctor
hudctl install
hudctl uninstall
hudctl start
hudctl stop
hudctl restart
hudctl reload              # SIGHUP: refresh collectors
hudctl run                 # foreground daemon (debug / systemd ExecStart)
hudctl status
hudctl status --json
hudctl theme list
hudctl theme set minimal   # or: developer
hudctl config              # open config in $EDITOR (or nano)
```

Logging: set `log_level` in config, or `HUDCTL_LOG_LEVEL` in the environment.

## What is collected

Enabled by default in `config.toml` `modules`:

| Module | Source | Notes |
|--------|--------|-------|
| `cwd` | process cwd | `~/...` display when under home |
| `git` | `.git` metadata | branch / dirty hints; optional cache |
| `cpu` | `/proc/stat` | percent from sample deltas |
| `memory` | `/proc/meminfo` | used / available / percent |
| `network` | `/proc/net/dev` | aggregate rx/tx bps (skips `lo`) |
| `clock` | local time | hhmm + ISO |

Optional modules (add to `modules` to enable):

| Module | Source | Notes |
|--------|--------|-------|
| `hostname` | stdlib | short + FQDN |
| `ssh` | env (`SSH_*`) | active session / client IP |
| `docker` | socket + cgroup | available / in-container |
| `kubernetes` | kubeconfig | current-context / in-cluster |
| `battery` | sysfs | capacity / status |
| `vpn` | `/sys/class/net` | tun/tap/wg-style interfaces |

## Themes

Packaged themes: `developer` (default), `minimal`.

Override or add themes in `~/.config/huddle/themes/*.toml`.

`hudctl theme set` only updates config; it does not by itself rewrite your
shell prompt.

## Prompt and window title (current limitation)

Renderers exist in the library (`bash`, `kitty`, `json`), but there is
**no** `hudctl prompt` or `hudctl title` command yet.

The bashrc block from `hudctl install` does **not** set `PS1` or the
terminal title. To drive a bash prompt from daemon state, use
`PROMPT_COMMAND` and `hudctl status --json` (see examples below).

### Example: set bash prompt (`PS1`)

`PS1` is the bash variable that holds your prompt text on Linux.

```bash
__hudctl_ps1() {
  local line
  line=$(hudctl status --json 2>/dev/null | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print("")
    raise SystemExit
s = d.get("sections") or {}
cwd = (s.get("cwd") or {}).get("display") or ""
git = s.get("git") or {}
branch = git.get("branch") or ""
dirty = "*" if git.get("dirty") else ""
clock = (s.get("clock") or {}).get("hhmm") or ""
parts = [p for p in (cwd, (branch + dirty) if branch else "", clock) if p]
print(" | ".join(parts))
' 2>/dev/null) || line=""
  if [ -n "$line" ]; then
    PS1="${line} \$ "
  else
    PS1="\u@\h:\w\$ "
  fi
}
PROMPT_COMMAND=__hudctl_ps1
```

### Example: set window title (Kitty / OSC)

```bash
set_kitty_title() {
  local title
  title=$(hudctl status --json 2>/dev/null | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print("-"); raise SystemExit
s = d.get("sections") or {}
cwd = (s.get("cwd") or {}).get("display") or "-"
git = s.get("git") or {}
branch = git.get("branch") if git.get("inside_repo") else "-"
clock = (s.get("clock") or {}).get("hhmm") or "-"
print(f"{cwd} | {branch} | {clock}")
' 2>/dev/null) || title="-"
  printf '\033]2;%s\007' "$title"
}
PROMPT_COMMAND=set_kitty_title
```

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
make            # help
make sync
make check      # ruff + mypy + pytest
make fmt
make build      # sdist + wheel in dist/
uv run hudctl version
```

## Architecture

Collectors gather structured context. The engine schedules and caches it.
Renderers transform snapshots into output and never collect system data.

See `PLAN.md` for design and roadmap.
See `docs/packaging.md` for build/release notes (PyPI publish is opt-in only).

## License

MIT
