"""Normalize unrestricted project scope to SQL NULL."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "i5e6f7a8b9c0"
down_revision: str | Sequence[str] | None = "h4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Treat legacy JSON null project scopes as unrestricted SQL NULL values."""
    op.execute(
        sa.text("UPDATE execution_plane.clusters SET project_ids = NULL WHERE project_ids = CAST('null' AS jsonb)")
    )
    op.execute(
        sa.text(
            "UPDATE execution_plane.cluster_bindings SET project_ids = NULL WHERE project_ids = CAST('null' AS jsonb)"
        )
    )


def downgrade() -> None:
    """Restore JSON null for compatibility with the preceding model mapping."""
    op.execute(
        sa.text("UPDATE execution_plane.clusters SET project_ids = CAST('null' AS jsonb) WHERE project_ids IS NULL")
    )
    op.execute(
        sa.text(
            "UPDATE execution_plane.cluster_bindings SET project_ids = CAST('null' AS jsonb) WHERE project_ids IS NULL"
        )
    )
