"""add_indexes_to_foreign_keys

Revision ID: 0b9dc23328e1
Revises: aa682db1eb3d
Create Date: 2025-12-14 13:59:27.188540

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0b9dc23328e1"
down_revision: Union[str, None] = "9a6c7f6b7d7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on versions.photo_uuid for faster photo version lookups
    op.create_index("ix_versions_photo_uuid", "versions", ["photo_uuid"], unique=False)

    # Add index on libraries.owner_id for faster library ownership queries
    op.create_index("ix_libraries_owner_id", "libraries", ["owner_id"], unique=False)

    # Add indexes on album_photos association table for faster album-photo joins
    op.create_index(
        "ix_album_photos_album_uuid", "album_photos", ["album_uuid"], unique=False
    )
    op.create_index(
        "ix_album_photos_photo_uuid", "album_photos", ["photo_uuid"], unique=False
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("ix_album_photos_photo_uuid", table_name="album_photos")
    op.drop_index("ix_album_photos_album_uuid", table_name="album_photos")
    op.drop_index("ix_libraries_owner_id", table_name="libraries")
    op.drop_index("ix_versions_photo_uuid", table_name="versions")
