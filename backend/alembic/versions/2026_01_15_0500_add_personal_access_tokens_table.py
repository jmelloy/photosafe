"""Add personal_access_tokens table

Revision ID: a1b2c3d4e5f6
Revises: 6324284fb717
Create Date: 2026-01-15 05:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6324284fb717"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create personal_access_tokens table
    op.create_table(
        "personal_access_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_personal_access_tokens_id"),
        "personal_access_tokens",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personal_access_tokens_user_id"),
        "personal_access_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personal_access_tokens_token_hash"),
        "personal_access_tokens",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_personal_access_tokens_token_hash"),
        table_name="personal_access_tokens",
    )
    op.drop_index(
        op.f("ix_personal_access_tokens_user_id"),
        table_name="personal_access_tokens",
    )
    op.drop_index(
        op.f("ix_personal_access_tokens_id"), table_name="personal_access_tokens"
    )

    # Drop table
    op.drop_table("personal_access_tokens")
