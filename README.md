# Syntara Execution Plane

The Execution Plane (EP) stores and runs work dispatched by Syntara. This repository owns the worker package, cluster and execution-target registries, work-item persistence, migrations for the `execution_plane` PostgreSQL schema, and the worker container image.

Syntara owns authentication, its public API facade, workflow dispatch, integrations, and the user interface. During this migration the Syntara application and EP worker still share a PostgreSQL database and the worker completes Temporal activities directly. The repositories are independent; the runtime service boundary is follow-up work documented in [`docs/integration.md`](docs/integration.md).

## Requirements

- Python 3.12, 3.13, or 3.14
- [`uv`](https://docs.astral.sh/uv/)
- PostgreSQL for migrations and local worker execution

## Development

```bash
uv sync --locked --all-groups
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy --strict src
```

Run the worker after setting `APP_DATABASE_URL` (or `DATABASE_URL`) and the Temporal connection settings:

```bash
uv run execution-plane-worker
```

Apply the EP migrations independently from Syntara's migration chain:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/database uv run alembic -c alembic.ini upgrade head
```

Build the worker image from this repository root:

```bash
podman build -f Containerfile -t localhost/execution-plane:dev .
```

The image runs as UID 1001 and starts `execution-plane-worker`. Set database and Temporal environment variables when running it.

## Ownership

Use this repository for EP worker, registry, migration, and placement changes. Make coordinated API, authorization, integration, and workflow changes in [Syntara](https://github.com/syntara-orchestration/syntara), and link the changes across pull requests.
