"""add database connections layer

Revision ID: 20260304_0004
Revises: 20260304_0003
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "20260304_0004"
down_revision: Union[str, None] = "20260304_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "active_connection_id" not in user_columns:
        op.add_column("users", sa.Column("active_connection_id", sa.Integer(), nullable=True))

    existing_tables = set(inspector.get_table_names())
    if "database_connections" not in existing_tables:
        op.create_table(
            "database_connections",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("db_type", sa.String(length=50), nullable=False, server_default="postgresql"),
            sa.Column("connection_url", sa.String(length=2048), nullable=False),
            sa.Column("is_shared", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_by", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_database_connections_id", "database_connections", ["id"], unique=False)
        op.create_index("ix_database_connections_name", "database_connections", ["name"], unique=False)
        op.create_index("ix_database_connections_created_by", "database_connections", ["created_by"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "database_connections" in existing_tables:
        index_names = {idx["name"] for idx in inspector.get_indexes("database_connections")}
        for index_name in [
            "ix_database_connections_created_by",
            "ix_database_connections_name",
            "ix_database_connections_id",
        ]:
            if index_name in index_names:
                op.drop_index(index_name, table_name="database_connections")
        op.drop_table("database_connections")

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "active_connection_id" in user_columns:
        op.drop_column("users", "active_connection_id")
