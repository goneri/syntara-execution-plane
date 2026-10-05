.PHONY: install test lint format typecheck migrate image secrets certs setup compose-up compose-down

install:
	uv sync --locked --all-groups

test:
	uv run pytest

lint:
	uv run ruff check src tests

format:
	uv run ruff format --check src tests

typecheck:
	uv run mypy --strict src

migrate:
	uv run alembic -c alembic.ini upgrade head

image:
	podman build -f Containerfile -t localhost/execution-plane:dev .

secrets:
	./tools/generate_secrets.sh

certs:
	uv run python tools/generate_certs.py

setup: install secrets certs

compose-up: setup
	uvx podman-compose -f compose.yaml up --build

compose-down:
	uvx podman-compose -f compose.yaml down
