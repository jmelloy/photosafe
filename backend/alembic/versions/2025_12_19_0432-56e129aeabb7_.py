"""empty message

Revision ID: 56e129aeabb7
Revises: 9e32c1812b65, d8e9f0a1b2c3
Create Date: 2025-12-19 04:32:41.728220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56e129aeabb7'
down_revision: Union[str, None] = ('9e32c1812b65', 'd8e9f0a1b2c3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
