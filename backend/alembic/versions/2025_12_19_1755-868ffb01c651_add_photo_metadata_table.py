"""add_photo_metadata_table

Revision ID: 868ffb01c651
Revises: 56e129aeabb7
Create Date: 2025-12-19 17:55:12.399914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '868ffb01c651'
down_revision: Union[str, None] = '56e129aeabb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create photo_metadata table
    op.create_table(
        'photo_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('photo_uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['photo_uuid'], ['photos.uuid'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('photo_uuid', 'key', name='uq_photo_metadata_photo_uuid_key')
    )
    
    # Add indexes for better query performance
    op.create_index(op.f('ix_photo_metadata_photo_uuid'), 'photo_metadata', ['photo_uuid'], unique=False)
    
    # Add GIN index on value field for efficient JSONB queries
    op.create_index('ix_photo_metadata_value_gin', 'photo_metadata', ['value'], unique=False, postgresql_using='gin')
    
    # Migrate existing search_info data to photo_metadata table
    # This query will flatten the JSONB search_info field into key-value pairs
    op.execute("""
        INSERT INTO photo_metadata (photo_uuid, key, value, source)
        SELECT 
            uuid,
            key,
            CASE 
                WHEN jsonb_typeof(value) = 'array' THEN value
                WHEN jsonb_typeof(value) = 'object' THEN value
                ELSE to_jsonb(value #>> '{}')
            END as value,
            'legacy' as source
        FROM photos,
        LATERAL jsonb_each(COALESCE(search_info, '{}'::jsonb))
        WHERE search_info IS NOT NULL AND search_info != 'null'::jsonb
        ON CONFLICT (photo_uuid, key) DO NOTHING
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_photo_metadata_value_gin', table_name='photo_metadata')
    op.drop_index(op.f('ix_photo_metadata_photo_uuid'), table_name='photo_metadata')
    
    # Drop table
    op.drop_table('photo_metadata')

