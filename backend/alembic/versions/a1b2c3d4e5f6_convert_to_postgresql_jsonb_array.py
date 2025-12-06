"""Convert to PostgreSQL with JSONB and ARRAY types

Revision ID: a1b2c3d4e5f6
Revises: 49348f7a48f6
Create Date: 2025-12-06 01:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '49348f7a48f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Convert Text columns to PostgreSQL-specific types (JSONB and ARRAY).
    This migration only applies when using PostgreSQL.
    For SQLite, this migration does nothing (columns remain as Text).
    
    Note: This migration assumes the database is starting fresh with PostgreSQL.
    If migrating existing SQLite data to PostgreSQL, you should:
    1. Export data from SQLite
    2. Create fresh PostgreSQL database
    3. Run migrations
    4. Import data with proper type conversion
    """
    # Get the database dialect
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Only apply PostgreSQL-specific changes if we're using PostgreSQL
    if dialect_name == 'postgresql':
        # Convert JSON string columns to JSONB and array columns to ARRAY
        # Note: This assumes columns are currently NULL or will be populated after migration
        # For data migration from SQLite, see MIGRATIONS.md
        with op.batch_alter_table('photos', schema=None) as batch_op:
            # Convert array fields from Text to ARRAY(String)
            # If migrating data, ensure array data is in PostgreSQL array format or NULL
            batch_op.alter_column('keywords',
                existing_type=sa.Text(),
                type_=postgresql.ARRAY(sa.String()),
                existing_nullable=True)
            
            batch_op.alter_column('labels',
                existing_type=sa.Text(),
                type_=postgresql.ARRAY(sa.String()),
                existing_nullable=True)
            
            batch_op.alter_column('albums',
                existing_type=sa.Text(),
                type_=postgresql.ARRAY(sa.String()),
                existing_nullable=True)
            
            batch_op.alter_column('persons',
                existing_type=sa.Text(),
                type_=postgresql.ARRAY(sa.String()),
                existing_nullable=True)
            
            # Convert JSON fields from Text to JSONB
            # If migrating data, ensure JSON data is valid JSON or NULL
            batch_op.alter_column('faces',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)
            
            batch_op.alter_column('place',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)
            
            batch_op.alter_column('exif',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)
            
            batch_op.alter_column('score',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)
            
            batch_op.alter_column('search_info',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)
            
            batch_op.alter_column('fields',
                existing_type=sa.Text(),
                type_=postgresql.JSONB(),
                existing_nullable=True)


def downgrade() -> None:
    """
    Convert PostgreSQL-specific types back to Text.
    This allows reverting to SQLite compatibility if needed.
    """
    # Get the database dialect
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Only apply PostgreSQL-specific changes if we're using PostgreSQL
    if dialect_name == 'postgresql':
        with op.batch_alter_table('photos', schema=None) as batch_op:
            # Convert ARRAY fields back to Text
            batch_op.alter_column('keywords',
                existing_type=postgresql.ARRAY(sa.String()),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('labels',
                existing_type=postgresql.ARRAY(sa.String()),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('albums',
                existing_type=postgresql.ARRAY(sa.String()),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('persons',
                existing_type=postgresql.ARRAY(sa.String()),
                type_=sa.Text(),
                existing_nullable=True)
            
            # Convert JSONB fields back to Text
            batch_op.alter_column('faces',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('place',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('exif',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('score',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('search_info',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
            
            batch_op.alter_column('fields',
                existing_type=postgresql.JSONB(),
                type_=sa.Text(),
                existing_nullable=True)
