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
