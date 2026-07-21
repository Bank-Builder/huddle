# Huddle / hudctl

Unified terminal context engine with pluggable renderers.

## Install

```bash
uv tool install hudctl
# or
pip install hudctl

hudctl install
hudctl start
hudctl status
```

Optional systemd user service (written by `hudctl install`):

```bash
systemctl --user daemon-reload
systemctl --user enable --now huddle.service
```

## Common commands

```bash
hudctl doctor
hudctl status --json
hudctl theme list
hudctl theme set minimal
hudctl config
hudctl reload
hudctl stop
```

Config lives at `~/.config/huddle/config.toml`.
Cache/state use XDG cache/state directories under `huddle/`.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv python pin 3.12
make sync
make check
uv run hudctl version
make build
```

## Architecture

Collectors gather structured context. The engine schedules and caches it.
Renderers (Kitty, Bash, JSON) turn snapshots into output without collecting.

See `PLAN.md` for the full design and roadmap.

## License

MIT
