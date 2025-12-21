"""Add search_data table for searchable metadata

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2025-12-21 20:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create search_data table with indexes and unique constraints"""
    # Create search_data table
    op.create_table(
        "search_data",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("photo_uuid", UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["photo_uuid"],
            ["photos.uuid"],
            ondelete="CASCADE",
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        "ix_search_data_photo_uuid", "search_data", ["photo_uuid"], unique=False
    )
    op.create_index("ix_search_data_key", "search_data", ["key"], unique=False)
    op.create_index("ix_search_data_value", "search_data", ["value"], unique=False)
    op.create_index(
        "ix_search_data_key_value", "search_data", ["key", "value"], unique=False
    )

    # Create unique constraint to prevent duplicate entries
    op.create_unique_constraint(
        "uq_search_data_photo_key_value",
        "search_data",
        ["photo_uuid", "key", "value"],
    )


def downgrade() -> None:
    """Drop search_data table and its indexes"""
    op.drop_table("search_data")
