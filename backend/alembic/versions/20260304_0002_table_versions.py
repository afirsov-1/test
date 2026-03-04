"""add table_versions for data rollback

Revision ID: 20260304_0002
Revises: 20260304_0001
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "20260304_0002"
down_revision: Union[str, None] = "20260304_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "table_versions" not in existing_tables:
        op.create_table(
            "table_versions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("table_name", sa.String(length=255), nullable=False),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("version_data", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_table_versions_id", "table_versions", ["id"], unique=False)
        op.create_index("ix_table_versions_user_id", "table_versions", ["user_id"], unique=False)
        op.create_index("ix_table_versions_table_name", "table_versions", ["table_name"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = set(inspector.get_table_names())
    if "table_versions" in existing_tables:
        index_names = {idx["name"] for idx in inspector.get_indexes("table_versions")}
        if "ix_table_versions_table_name" in index_names:
            op.drop_index("ix_table_versions_table_name", table_name="table_versions")
        if "ix_table_versions_user_id" in index_names:
            op.drop_index("ix_table_versions_user_id", table_name="table_versions")
        if "ix_table_versions_id" in index_names:
            op.drop_index("ix_table_versions_id", table_name="table_versions")
        op.drop_table("table_versions")
