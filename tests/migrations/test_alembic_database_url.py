"""Alembic ConfigParser cannot store percent-encoded database URLs.

Konflux builds migrator-url with urllib.parse.quote, so passwords that contain
``{`` become ``%7B…%7D``. env.py must not pass that string to
``Config.set_main_option``.
"""

from __future__ import annotations

import pytest
from alembic.config import Config
from sqlalchemy.engine import make_url

_PERCENT_ENCODED_URL = (
    "postgresql+asyncpg://execution_plane_migrator:"
    "%7B817bf76e34f2077d43fd75b72f865c13c4e1e26450a50480%7D"
    "@ao-postgres.aap27-next.svc:5432/execution_plane"
)


def test_alembic_config_rejects_percent_encoded_sqlalchemy_url() -> None:
    cfg = Config()
    with pytest.raises(ValueError, match="invalid interpolation syntax"):
        cfg.set_main_option("sqlalchemy.url", _PERCENT_ENCODED_URL)


def test_percent_encoded_migrator_url_is_a_valid_sqlalchemy_url() -> None:
    parsed = make_url(_PERCENT_ENCODED_URL)
    assert parsed.password == "{817bf76e34f2077d43fd75b72f865c13c4e1e26450a50480}"  # noqa: S105
    assert parsed.host == "ao-postgres.aap27-next.svc"
    assert parsed.database == "execution_plane"
