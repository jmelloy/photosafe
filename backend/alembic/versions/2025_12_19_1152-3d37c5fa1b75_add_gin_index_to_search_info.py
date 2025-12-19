"""add_gin_index_to_search_info

Revision ID: 3d37c5fa1b75
Revises: 56e129aeabb7
Create Date: 2025-12-19 11:52:20.247991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d37c5fa1b75'
down_revision: Union[str, None] = '56e129aeabb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add GIN index on search_info JSONB field for efficient full-text search
    # GIN indexes are optimal for JSONB fields in PostgreSQL
    op.create_index(
        "ix_photos_search_info_gin",
        "photos",
        ["search_info"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    # Drop the GIN index on search_info
    op.drop_index("ix_photos_search_info_gin", table_name="photos")
