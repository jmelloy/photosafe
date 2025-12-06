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

2. Run migrations to create the database tables:
```bash
alembic upgrade head
```

This will create the `photosafe.db` SQLite database with all necessary tables.

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

The database URL is configured in `app/database.py`:
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./photosafe.db"
```

This URL is automatically used by Alembic through the configuration in `alembic/env.py`.

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

3. Apply the migration:
```bash
alembic upgrade head
```

### Changing Column Type

1. Modify the column in your model
2. Generate migration: `alembic revision --autogenerate -m "Change column type"`
3. Review and potentially modify the migration (SQLite has limitations on ALTER TABLE)
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
```bash
rm photosafe.db
alembic upgrade head
```

**Warning**: This will delete all data!

## Integration with Application

The application no longer uses `Base.metadata.create_all()` for table creation. Instead:

1. Database schema is managed entirely through Alembic migrations
2. On first deployment, run `alembic upgrade head` to create tables
3. For schema changes, create and apply migrations

## Comparison with Django Migrations

If you're familiar with Django migrations, here's a quick comparison:

| Django | Alembic |
|--------|---------|
| `python manage.py makemigrations` | `alembic revision --autogenerate -m "message"` |
| `python manage.py migrate` | `alembic upgrade head` |
| `python manage.py showmigrations` | `alembic history` |
| `python manage.py migrate app_name zero` | `alembic downgrade base` |

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Auto Generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
