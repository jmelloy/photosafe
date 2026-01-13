"""Add unique constraint on latitude longitude to place_summaries

Revision ID: 6324284fb717
Revises: 622445ac768c
Create Date: 2026-01-13 09:35:49.907899

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6324284fb717"
down_revision: Union[str, None] = "622445ac768c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unique index on place_name and recreate as non-unique
    op.drop_index("ix_place_summaries_place_name", table_name="place_summaries")
    op.create_index(
        op.f("ix_place_summaries_place_name"),
        "place_summaries",
        ["place_name"],
        unique=False,
    )

    # Add indices for latitude and longitude if they don't exist
    op.create_index(
        op.f("ix_place_summaries_latitude"),
        "place_summaries",
        ["latitude"],
        unique=False,
    )
    op.create_index(
        op.f("ix_place_summaries_longitude"),
        "place_summaries",
        ["longitude"],
        unique=False,
    )

    # Add unique constraint on (latitude, longitude)
    op.create_unique_constraint(
        "uq_place_summaries_lat_lon", "place_summaries", ["latitude", "longitude"]
    )


def downgrade() -> None:
    from sqlalchemy.exc import ProgrammingError

    # Drop unique constraint on (latitude, longitude)
    op.drop_constraint("uq_place_summaries_lat_lon", "place_summaries", type_="unique")

    # Drop indices for latitude and longitude (these were created by this migration)
    # Use try-except since these might not exist in all database states
    bind = op.get_bind()
    try:
        bind.execute(sa.text("DROP INDEX IF EXISTS ix_place_summaries_longitude"))
    except ProgrammingError:
        pass

    try:
        bind.execute(sa.text("DROP INDEX IF EXISTS ix_place_summaries_latitude"))
    except ProgrammingError:
        pass

    # Restore unique index on place_name
    # Drop non-unique index first, then recreate as unique
    op.drop_index(op.f("ix_place_summaries_place_name"), table_name="place_summaries")
    op.create_index(
        "ix_place_summaries_place_name", "place_summaries", ["place_name"], unique=True
    )
