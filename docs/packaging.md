# Packaging and release

Distribution name on PyPI: **`hudctl`** (not `huddle`).

## Local build

```bash
make sync
make check
make build
```

Artifacts land in `dist/` (`hudctl-*-py3-none-any.whl` and sdist).

Smoke-install a local wheel:

```bash
uv venv /tmp/hudctl-smoke
uv pip install --python /tmp/hudctl-smoke dist/hudctl-*.whl
/tmp/hudctl-smoke/bin/hudctl version
```

## CI

- `ci.yml` runs `make sync`, `make check`, and `make build` on Python 3.12/3.13
- `release.yml` runs on `v*` tags: check, build, upload `dist` artifacts
- PyPI publish is **not** automatic on tags

## Publishing (manual, opt-in)

Publishing requires a workflow_dispatch run with `publish_pypi=true` and a
configured GitHub Environment named `pypi` with Trusted Publishing on PyPI.

Do not publish until ready. For a dry run against TestPyPI (when desired):

```bash
uv build --no-sources
uv publish --index testpypi
```

Then smoke:

```bash
uv tool install --index https://test.pypi.org/simple/ --index-strategy unsafe-best-match hudctl
hudctl version
```
