"""Add task and place_summary tables for photo processing

Revision ID: e1f2a3b4c5d6
Revises: d8e9f0a1b2c3
Create Date: 2025-12-20 19:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=True),
        sa.Column("processed", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)
    op.create_index(op.f("ix_tasks_task_type"), "tasks", ["task_type"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)

    # Create place_summaries table
    op.create_table(
        "place_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("place_name", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("photo_count", sa.Integer(), nullable=False),
        sa.Column("first_photo_date", sa.DateTime(), nullable=True),
        sa.Column("last_photo_date", sa.DateTime(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("state_province", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("place_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("place_name"),
    )
    op.create_index(op.f("ix_place_summaries_id"), "place_summaries", ["id"], unique=False)
    op.create_index(op.f("ix_place_summaries_place_name"), "place_summaries", ["place_name"], unique=True)
    op.create_index(op.f("ix_place_summaries_country"), "place_summaries", ["country"], unique=False)
    op.create_index(op.f("ix_place_summaries_state_province"), "place_summaries", ["state_province"], unique=False)
    op.create_index(op.f("ix_place_summaries_city"), "place_summaries", ["city"], unique=False)


def downgrade() -> None:
    # Drop place_summaries table
    op.drop_index(op.f("ix_place_summaries_city"), table_name="place_summaries")
    op.drop_index(op.f("ix_place_summaries_state_province"), table_name="place_summaries")
    op.drop_index(op.f("ix_place_summaries_country"), table_name="place_summaries")
    op.drop_index(op.f("ix_place_summaries_place_name"), table_name="place_summaries")
    op.drop_index(op.f("ix_place_summaries_id"), table_name="place_summaries")
    op.drop_table("place_summaries")

    # Drop tasks table
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_task_type"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_table("tasks")
