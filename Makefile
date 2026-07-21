.PHONY: help sync lint fmt check test typecheck build

help:
	@echo "Targets:"
	@echo "  sync       Install/sync deps with uv"
	@echo "  lint       Ruff check + format check"
	@echo "  fmt        Ruff format"
	@echo "  typecheck  mypy"
	@echo "  test       pytest with coverage"
	@echo "  check      lint + typecheck + test"
	@echo "  build      Build sdist and wheel"

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
