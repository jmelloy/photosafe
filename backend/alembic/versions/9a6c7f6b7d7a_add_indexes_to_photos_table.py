"""add_indexes_to_photos_table

Revision ID: 9a6c7f6b7d7a
Revises: c71fdf3b7df8
Create Date: 2025-12-13 15:41:56.700388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a6c7f6b7d7a"
down_revision: Union[str, None] = "c71fdf3b7df8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for commonly filtered and joined columns

    # Foreign key indexes for joins and ownership filtering
    op.create_index("ix_photos_owner_id", "photos", ["owner_id"], unique=False)
    op.create_index("ix_photos_library_id", "photos", ["library_id"], unique=False)

    # Date index for ordering and date range filtering (most common query pattern)
    op.create_index("ix_photos_date", "photos", ["date"], unique=False)

    # GIN indexes for array containment queries (PostgreSQL specific)
    # These are used for filtering by albums, keywords, and persons
    op.create_index(
        "ix_photos_albums_gin",
        "photos",
        ["albums"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_photos_keywords_gin",
        "photos",
        ["keywords"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_photos_persons_gin",
        "photos",
        ["persons"],
        unique=False,
        postgresql_using="gin",
    )

    # Index for masterFingerprint (used for deduplication)
    op.create_index(
        "ix_photos_master_fingerprint",
        "photos",
        ["masterFingerprint"],
        unique=False,
    )

    # Boolean flag indexes for common filters
    op.create_index("ix_photos_favorite", "photos", ["favorite"], unique=False)
    op.create_index("ix_photos_isphoto", "photos", ["isphoto"], unique=False)
    op.create_index("ix_photos_ismovie", "photos", ["ismovie"], unique=False)
    op.create_index("ix_photos_screenshot", "photos", ["screenshot"], unique=False)
    op.create_index("ix_photos_panorama", "photos", ["panorama"], unique=False)
    op.create_index("ix_photos_portrait", "photos", ["portrait"], unique=False)

    # Composite index for location queries (both latitude and longitude together)
    op.create_index(
        "ix_photos_location",
        "photos",
        ["latitude", "longitude"],
        unique=False,
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("ix_photos_location", table_name="photos")
    op.drop_index("ix_photos_portrait", table_name="photos")
    op.drop_index("ix_photos_panorama", table_name="photos")
    op.drop_index("ix_photos_screenshot", table_name="photos")
    op.drop_index("ix_photos_ismovie", table_name="photos")
    op.drop_index("ix_photos_isphoto", table_name="photos")
    op.drop_index("ix_photos_favorite", table_name="photos")
    op.drop_index("ix_photos_master_fingerprint", table_name="photos")
    op.drop_index("ix_photos_persons_gin", table_name="photos")
    op.drop_index("ix_photos_keywords_gin", table_name="photos")
    op.drop_index("ix_photos_albums_gin", table_name="photos")
    op.drop_index("ix_photos_date", table_name="photos")
    op.drop_index("ix_photos_library_id", table_name="photos")
    op.drop_index("ix_photos_owner_id", table_name="photos")
