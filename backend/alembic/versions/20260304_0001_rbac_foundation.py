"""rbac foundation: add user role and table permissions

Revision ID: 20260304_0001
Revises: 
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "20260304_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "role" not in user_columns:
        op.add_column(
            "users",
            sa.Column("role", sa.String(length=50), nullable=False, server_default="operator"),
        )

    existing_tables = set(inspector.get_table_names())
    if "table_permissions" not in existing_tables:
        op.create_table(
            "table_permissions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("table_name", sa.String(length=255), nullable=False),
            sa.Column("can_read", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("can_write", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("can_alter", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("can_delete", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_owner", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("blocked_until", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_table_permissions_id", "table_permissions", ["id"], unique=False)
        op.create_index("ix_table_permissions_user_id", "table_permissions", ["user_id"], unique=False)
        op.create_index("ix_table_permissions_table_name", "table_permissions", ["table_name"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "table_permissions" in existing_tables:
        index_names = {idx["name"] for idx in inspector.get_indexes("table_permissions")}
        if "ix_table_permissions_table_name" in index_names:
            op.drop_index("ix_table_permissions_table_name", table_name="table_permissions")
        if "ix_table_permissions_user_id" in index_names:
            op.drop_index("ix_table_permissions_user_id", table_name="table_permissions")
        if "ix_table_permissions_id" in index_names:
            op.drop_index("ix_table_permissions_id", table_name="table_permissions")
        op.drop_table("table_permissions")

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "role" in user_columns:
        op.drop_column("users", "role")
