"""Merge execution-target placement and payload/fencing migration branches."""

from collections.abc import Sequence

revision: str = "h4d5e6f7a8b9"
down_revision: str | Sequence[str] | None = ("e0f1a2b3c4d5", "g3c4d5e6f7a8")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Join the independent placement and encrypted-payload histories."""


def downgrade() -> None:
    """Leave both histories available when reverting the merge point."""
