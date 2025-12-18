"""convert_uuid_fields_to_postgres_uuid

Revision ID: 9e32c1812b65
Revises: 0b9dc23328e1
Create Date: 2025-12-17 18:02:08.096256

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "9e32c1812b65"
down_revision: Union[str, None] = "0b9dc23328e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert UUID fields from String to PostgreSQL UUID type
    # We need to use USING clause to cast string values to UUID

    # 1. Drop foreign key constraints that reference uuid columns
    op.drop_constraint("versions_photo_uuid_fkey", "versions", type_="foreignkey")
    op.drop_constraint(
        "album_photos_album_uuid_fkey", "album_photos", type_="foreignkey"
    )
    op.drop_constraint(
        "album_photos_photo_uuid_fkey", "album_photos", type_="foreignkey"
    )

    op.execute(
        "delete from photos where lower(uuid) in (select lower(uuid) from photos group by lower(uuid) having count(*) > 1)"
    )

    # 2. Convert photos.uuid (primary key)
    op.execute("ALTER TABLE photos ALTER COLUMN uuid TYPE UUID USING uuid::uuid")

    # 3. Convert albums.uuid (primary key)
    op.execute("ALTER TABLE albums ALTER COLUMN uuid TYPE UUID USING uuid::uuid")

    op.execute(
        "delete from versions where not exists (select 1 from photos where photos.uuid = versions.photo_uuid::uuid)"
    )

    # 4. Convert versions.photo_uuid (foreign key)
    op.execute(
        "ALTER TABLE versions ALTER COLUMN photo_uuid TYPE UUID USING photo_uuid::uuid"
    )

    op.execute(
        "delete from album_photos where not exists (select 1 from photos where photos.uuid = album_photos.photo_uuid::uuid)"
    )

    # 5. Convert album_photos association table columns
    op.execute(
        "ALTER TABLE album_photos ALTER COLUMN album_uuid TYPE UUID USING album_uuid::uuid"
    )
    op.execute(
        "ALTER TABLE album_photos ALTER COLUMN photo_uuid TYPE UUID USING photo_uuid::uuid"
    )

    # 6. Recreate foreign key constraints
    op.create_foreign_key(
        "fk_versions_photo_uuid", "versions", "photos", ["photo_uuid"], ["uuid"]
    )
    op.create_foreign_key(
        "album_photos_album_uuid_fkey",
        "album_photos",
        "albums",
        ["album_uuid"],
        ["uuid"],
    )
    op.create_foreign_key(
        "album_photos_photo_uuid_fkey",
        "album_photos",
        "photos",
        ["photo_uuid"],
        ["uuid"],
    )


def downgrade() -> None:
    # Revert UUID fields back to String type

    # 1. Drop foreign key constraints
    op.drop_constraint("fk_versions_photo_uuid", "versions", type_="foreignkey")
    op.drop_constraint(
        "album_photos_album_uuid_fkey", "album_photos", type_="foreignkey"
    )
    op.drop_constraint(
        "album_photos_photo_uuid_fkey", "album_photos", type_="foreignkey"
    )

    # 2. Convert back to String
    op.execute("ALTER TABLE photos ALTER COLUMN uuid TYPE VARCHAR USING uuid::text")
    op.execute("ALTER TABLE albums ALTER COLUMN uuid TYPE VARCHAR USING uuid::text")
    op.execute(
        "ALTER TABLE versions ALTER COLUMN photo_uuid TYPE VARCHAR USING photo_uuid::text"
    )
    op.execute(
        "ALTER TABLE album_photos ALTER COLUMN album_uuid TYPE VARCHAR USING album_uuid::text"
    )
    op.execute(
        "ALTER TABLE album_photos ALTER COLUMN photo_uuid TYPE VARCHAR USING photo_uuid::text"
    )

    # 3. Recreate foreign key constraints
    op.create_foreign_key(
        "fk_versions_photo_uuid", "versions", "photos", ["photo_uuid"], ["uuid"]
    )
    op.create_foreign_key(
        "album_photos_album_uuid_fkey",
        "album_photos",
        "albums",
        ["album_uuid"],
        ["uuid"],
    )
    op.create_foreign_key(
        "album_photos_photo_uuid_fkey",
        "album_photos",
        "photos",
        ["photo_uuid"],
        ["uuid"],
    )
