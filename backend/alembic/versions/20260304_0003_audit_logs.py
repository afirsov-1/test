"""add audit logs table

Revision ID: 20260304_0003
Revises: 20260304_0002
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "20260304_0003"
down_revision: Union[str, None] = "20260304_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "audit_logs" not in existing_tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=255), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("entity_type", sa.String(length=100), nullable=False),
            sa.Column("entity_name", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="success"),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_logs_id", "audit_logs", ["id"], unique=False)
        op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
        op.create_index("ix_audit_logs_username", "audit_logs", ["username"], unique=False)
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
        op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"], unique=False)
        op.create_index("ix_audit_logs_entity_name", "audit_logs", ["entity_name"], unique=False)
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "audit_logs" in existing_tables:
        index_names = {idx["name"] for idx in inspector.get_indexes("audit_logs")}
        for index_name in [
            "ix_audit_logs_created_at",
            "ix_audit_logs_entity_name",
            "ix_audit_logs_entity_type",
            "ix_audit_logs_action",
            "ix_audit_logs_username",
            "ix_audit_logs_user_id",
            "ix_audit_logs_id",
        ]:
            if index_name in index_names:
                op.drop_index(index_name, table_name="audit_logs")
        op.drop_table("audit_logs")
