# Huddle / hudctl

Unified terminal context engine with pluggable renderers.

## Install

```bash
uv tool install hudctl
# or
pip install hudctl
```

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv python pin 3.12
make sync
make check
uv run hudctl version
make build
```

## License

MIT
