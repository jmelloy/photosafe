# Database Migrations with Alembic

This FastAPI backend now uses Alembic for database migrations, providing a structured way to manage database schema changes over time.

## Overview

Alembic is a lightweight database migration tool for use with SQLAlchemy. It allows you to:
- Track database schema changes over time
- Apply migrations incrementally
- Rollback changes if needed
- Generate migrations automatically from model changes

## Prerequisites

Alembic is included in the `requirements.txt` file and will be installed automatically when you run:

```bash
pip install -r requirements.txt
```

## Initial Setup

When setting up the application for the first time:

1. Navigate to the backend directory:
```bash
cd backend
```

2. Configure your database connection by setting the `DATABASE_URL` environment variable:
```bash
# For PostgreSQL:
export DATABASE_URL="postgresql://user:password@localhost:5432/photosafe"
```

3. Run migrations to create the database tables:
```bash
alembic upgrade head
```

This will create the database with all necessary tables in the specified PostgreSQL database.

## Migration Commands

### Applying Migrations

To apply all pending migrations:
```bash
alembic upgrade head
```

To upgrade to a specific revision:
```bash
alembic upgrade <revision_id>
```

### Viewing Migration History

To see the current migration version:
```bash
alembic current
```

To see the migration history:
```bash
alembic history
```

To see pending migrations:
```bash
alembic history --verbose
```

### Rollback Migrations

To downgrade one migration:
```bash
alembic downgrade -1
```

To downgrade to a specific revision:
```bash
alembic downgrade <revision_id>
```

To rollback all migrations:
```bash
alembic downgrade base
```

## Creating New Migrations

When you make changes to the models in `app/models.py`:

### Automatic Migration Generation

1. Make your changes to the model files
2. Generate a new migration automatically:
```bash
alembic revision --autogenerate -m "Description of changes"
```

3. Review the generated migration file in `alembic/versions/`
4. Apply the migration:
```bash
alembic upgrade head
```

### Manual Migration Creation

If you need to create a migration manually:

```bash
alembic revision -m "Description of changes"
```

Then edit the generated file in `alembic/versions/` to add your upgrade and downgrade logic.

## Migration File Structure

Migration files are located in `alembic/versions/` and have the following structure:

```python
"""Description of changes

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = 'xyz789'

def upgrade():
    # Commands to apply the migration
    pass

def downgrade():
    # Commands to rollback the migration
    pass
```

## Configuration

### Database URL

The database URL is configured via the `DATABASE_URL` environment variable in `app/database.py`:

**PostgreSQL:**
```python
DATABASE_URL = "postgresql://user:password@host:5432/database"
```

This URL is automatically used by Alembic through the configuration in `alembic/env.py`.

The application uses PostgreSQL native `JSONB` and `ARRAY(String)` types for better performance and querying.

### Alembic Configuration

The main Alembic configuration file is `alembic.ini`. Key settings:
- `script_location`: Location of migration scripts (default: `alembic/`)
- Migration files are auto-generated in `alembic/versions/`

## Migration Best Practices

1. **Always review auto-generated migrations**: Alembic's autogenerate is smart but not perfect. Always review the generated migration file before applying it.

2. **Test migrations**: Test migrations in a development environment before applying to production.

3. **Write reversible migrations**: Always implement both `upgrade()` and `downgrade()` functions so you can rollback if needed.

4. **Use descriptive names**: Give your migrations clear, descriptive names that explain what changed.

5. **Commit migrations to version control**: Migration files should be committed to git along with model changes.

6. **Don't modify existing migrations**: Once a migration has been applied in production, don't modify it. Create a new migration instead.

## Common Scenarios

### Adding a New Column

1. Add the column to your model in `app/models.py`:
```python
class Photo(Base):
    # ... existing columns ...
    new_field = Column(String, nullable=True)
```

2. Generate the migration:
```bash
alembic revision --autogenerate -m "Add new_field to Photo model"
```

3. Review the generated migration file in `alembic/versions/`

4. Apply the migration:
```bash
alembic upgrade head
```

### Changing Column Type

1. Modify the column in your model
2. Generate migration: `alembic revision --autogenerate -m "Change column type"`
3. Review the generated migration file
4. Apply: `alembic upgrade head`

### Adding a New Table

1. Add the new model class in `app/models.py`
2. Import the model in `alembic/env.py` if not already imported
3. Generate: `alembic revision --autogenerate -m "Add NewTable model"`
4. Apply: `alembic upgrade head`

## Troubleshooting

### "Target database is not up to date"

This means there are pending migrations. Run:
```bash
alembic upgrade head
```

### "Can't locate revision identified by 'xyz'"

This usually means the migration file is missing or the database version table is out of sync. Check:
1. All migration files are present in `alembic/versions/`
2. The `alembic_version` table in the database

### Starting Fresh

To completely reset the database:

**PostgreSQL:**
```bash
# Drop and recreate the database
dropdb photosafe
createdb photosafe
alembic upgrade head
```

**Warning**: This will delete all data!

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
