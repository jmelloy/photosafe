"""Add apple_credentials and apple_auth_sessions tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-18 01:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create apple_credentials table
    op.create_table(
        "apple_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("apple_id", sa.String(), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_2fa", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_authenticated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for apple_credentials
    op.create_index(
        op.f("ix_apple_credentials_id"),
        "apple_credentials",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_apple_credentials_user_id"),
        "apple_credentials",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_apple_credentials_apple_id"),
        "apple_credentials",
        ["apple_id"],
        unique=False,
    )

    # Create apple_auth_sessions table
    op.create_table(
        "apple_auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.Integer(), nullable=False),
        sa.Column("session_data", JSONB, nullable=True),
        sa.Column(
            "is_authenticated", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("requires_2fa", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "awaiting_2fa_code", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("trusted_devices", JSONB, nullable=True),
        sa.Column("session_token", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["credential_id"], ["apple_credentials.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for apple_auth_sessions
    op.create_index(
        op.f("ix_apple_auth_sessions_id"),
        "apple_auth_sessions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_apple_auth_sessions_credential_id"),
        "apple_auth_sessions",
        ["credential_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_apple_auth_sessions_session_token"),
        "apple_auth_sessions",
        ["session_token"],
        unique=True,
    )


def downgrade() -> None:
    # Drop apple_auth_sessions indexes
    op.drop_index(
        op.f("ix_apple_auth_sessions_session_token"),
        table_name="apple_auth_sessions",
    )
    op.drop_index(
        op.f("ix_apple_auth_sessions_credential_id"),
        table_name="apple_auth_sessions",
    )
    op.drop_index(
        op.f("ix_apple_auth_sessions_id"),
        table_name="apple_auth_sessions",
    )

    # Drop apple_auth_sessions table
    op.drop_table("apple_auth_sessions")

    # Drop apple_credentials indexes
    op.drop_index(
        op.f("ix_apple_credentials_apple_id"),
        table_name="apple_credentials",
    )
    op.drop_index(
        op.f("ix_apple_credentials_user_id"),
        table_name="apple_credentials",
    )
    op.drop_index(
        op.f("ix_apple_credentials_id"),
        table_name="apple_credentials",
    )

    # Drop apple_credentials table
    op.drop_table("apple_credentials")
