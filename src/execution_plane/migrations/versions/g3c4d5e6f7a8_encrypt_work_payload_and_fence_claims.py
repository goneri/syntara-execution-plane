"""Encrypt stored invocation payloads and fence worker claims."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import select, update

from execution_plane.models.encrypted_payload import EncryptedWorkItemPayload

revision = "g3c4d5e6f7a8"
down_revision = "f2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Encrypt pre-existing payloads with the configured EP key and add claim fencing."""
    op.add_column("work_items", sa.Column("claim_owner_id", sa.Uuid(), nullable=True), schema="execution_plane")
    op.add_column(
        "work_items",
        sa.Column("claim_generation", sa.Integer(), server_default="0", nullable=False),
        schema="execution_plane",
    )
    op.add_column(
        "work_items", sa.Column("backend_resource_name", sa.String(253), nullable=True), schema="execution_plane"
    )
    op.add_column(
        "work_items", sa.Column("backend_resource_uid", sa.String(64), nullable=True), schema="execution_plane"
    )
    op.add_column(
        "work_items",
        sa.Column("resource_cleanup_status", sa.String(32), server_default="not_required", nullable=False),
        schema="execution_plane",
    )
    op.add_column(
        "work_items", sa.Column("resource_cleanup_error", sa.String(1000), nullable=True), schema="execution_plane"
    )
    connection = op.get_bind()
    table = sa.Table("work_items", sa.MetaData(), schema="execution_plane", autoload_with=connection)
    payload_type = EncryptedWorkItemPayload()
    for row in connection.execute(select(table.c.id, table.c.payload)).mappings():
        payload = row["payload"]
        if isinstance(payload, dict) and "_ep_encrypted_payload_v1" in payload:
            continue
        encrypted = payload_type.process_bind_param(payload, connection.dialect)
        connection.execute(update(table).where(table.c.id == row["id"]).values(payload=encrypted))


def downgrade() -> None:
    """Restore readable JSONB payloads before removing worker claim fencing."""
    connection = op.get_bind()
    table = sa.Table("work_items", sa.MetaData(), schema="execution_plane", autoload_with=connection)
    payload_type = EncryptedWorkItemPayload()
    for row in connection.execute(select(table.c.id, table.c.payload)).mappings():
        value = payload_type.process_result_value(row["payload"], connection.dialect)
        connection.execute(update(table).where(table.c.id == row["id"]).values(payload=value))
    op.drop_column("work_items", "claim_generation", schema="execution_plane")
    op.drop_column("work_items", "claim_owner_id", schema="execution_plane")
    op.drop_column("work_items", "backend_resource_name", schema="execution_plane")
    op.drop_column("work_items", "backend_resource_uid", schema="execution_plane")
    op.drop_column("work_items", "resource_cleanup_status", schema="execution_plane")
    op.drop_column("work_items", "resource_cleanup_error", schema="execution_plane")
