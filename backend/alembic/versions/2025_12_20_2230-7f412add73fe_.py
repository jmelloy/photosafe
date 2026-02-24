"""empty message

Revision ID: 7f412add73fe
Revises: 56e129aeabb7, e1f2a3b4c5d6
Create Date: 2025-12-20 22:30:41.208616

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "7f412add73fe"
down_revision: Union[str, None] = ("56e129aeabb7", "e1f2a3b4c5d6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
