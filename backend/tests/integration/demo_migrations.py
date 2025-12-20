#!/usr/bin/env python
"""
Demo script to test Alembic migrations with the FastAPI backend.

This script demonstrates:
1. Checking migration status
2. Running migrations
3. Creating test data
4. Verifying data persistence

NOTE: Requires PostgreSQL database to be running.
"""

import subprocess
import sys
import os
from pathlib import Path
from sqlalchemy import select
from datetime import datetime, timezone

# Change to backend directory
backend_dir = Path(__file__).parent
os.chdir(backend_dir)


def run_command(cmd, description):
    """Run a shell command and print the result"""
    print(f"\n{'=' * 60}")
    print(f"▶ {description}")
    print(f"{'=' * 60}")
    print(f"Command: {cmd}")
    print()

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print("✅ Success")
        return True


def main():
    print("=" * 60)
    print("Alembic Migration Demo for PhotoSafe FastAPI Backend")
    print("=" * 60)

    # Verify DATABASE_URL is set to PostgreSQL
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url.startswith("postgresql"):
        print("\n❌ ERROR: DATABASE_URL must be set to a PostgreSQL connection string")
        print(
            "Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/photosafe'"
        )
        return 1

    # 1. Check current migration status
    if not run_command("alembic current", "Checking current migration status"):
        return 1

    # 2. Show migration history
    if not run_command("alembic history", "Showing migration history"):
        return 1

    # 3. Run migrations
    if not run_command("alembic upgrade head", "Applying migrations"):
        return 1

    # 4. Verify database tables were created using psql
    if not run_command("psql \"$DATABASE_URL\" -c '\\dt'", "Verifying database tables"):
        return 1

    # 5. Create test data using Python
    print(f"\n{'=' * 60}")
    print("▶ Creating test data")
    print(f"{'=' * 60}")

    from app.database import SessionLocal
    from app.models import User
    from app.auth import get_password_hash

    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.exec(select(User).where(User.username == "testuser")).first()
        if existing_user:
            print("User 'testuser' already exists")
        else:
            # Create a test user
            test_user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpass123"),
                name="Test User",
                is_active=True,
                is_superuser=False,
                date_joined=datetime.now(timezone.utc),
            )
            db.add(test_user)
            db.commit()
            print(f"✅ Created test user: {test_user.username}")

        # Verify data
        user_count = len(db.exec(select(User)).all())
        print(f"✅ Total users in database: {user_count}")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

    # 6. Test rollback (optional - commented out to preserve data)
    # print(f"\n{'='*60}")
    # print("▶ Testing migration rollback (optional)")
    # print(f"{'='*60}")
    # if not run_command("alembic downgrade -1", "Rolling back one migration"):
    #     return 1
    # if not run_command("alembic upgrade head", "Re-applying migration"):
    #     return 1

    print(f"\n{'=' * 60}")
    print("✅ All migration tests passed successfully!")
    print(f"{'=' * 60}")
    print("\nNext steps:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print(
        "2. Create new migrations when models change: alembic revision --autogenerate -m 'Description'"
    )
    print("3. Apply migrations: alembic upgrade head")
    print("\nFor more information, see MIGRATIONS.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
