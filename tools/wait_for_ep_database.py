"""Block until the Execution Plane database accepts connections.

podman-compose starts dependent containers as soon as a required container exists,
so compose healthchecks cannot order bootstrap. Callers wait here instead.
"""

from __future__ import annotations

import asyncio
import os
import time

import asyncpg
from sqlalchemy.engine import make_url

_DEFAULT_TIMEOUT_SECONDS = 180.0
_RETRY_PAUSE_SECONDS = 2.0


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("EP_DATABASE_URL")
    if not url:
        msg = "DATABASE_URL or EP_DATABASE_URL is required"
        raise SystemExit(msg)
    return make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)


async def _ready(dsn: str, sql: str | None) -> None:
    conn = await asyncpg.connect(dsn)
    try:
        if sql:
            result = await conn.fetchval(sql)
            if result is None:
                msg = f"query returned no row: {sql}"
                raise RuntimeError(msg)
    finally:
        await conn.close()


async def wait_for_database() -> None:
    """Retry until the DSN connects, and until WAIT_FOR_SQL succeeds when set."""
    dsn = _dsn()
    sql = os.environ.get("WAIT_FOR_SQL") or None
    timeout = float(os.environ.get("WAIT_FOR_DATABASE_SECONDS", _DEFAULT_TIMEOUT_SECONDS))
    deadline = time.monotonic() + timeout
    last_error = "not attempted"
    while time.monotonic() < deadline:
        try:
            await _ready(dsn, sql)
            return
        except Exception as exc:  # noqa: BLE001 — bootstrap races any connect failure
            last_error = str(exc)
            print(f"Waiting for database: {last_error}", flush=True)
            await asyncio.sleep(_RETRY_PAUSE_SECONDS)
    msg = f"Timed out waiting for database: {last_error}"
    raise SystemExit(msg)


if __name__ == "__main__":
    asyncio.run(wait_for_database())
