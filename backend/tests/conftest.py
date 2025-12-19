"""Shared test fixtures and configuration."""

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.database import get_db
from app.main import app
from app.models import User, Library, Photo, Version, Album, PhotoMetadata, album_photos
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

# Define the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"

# Test database URL - defaults to localhost:5433 (test-db container)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5433/photosafe_test",
)


def run_migrations(database_url: str):
    """Run alembic migrations for the test database."""
    # Save the current DATABASE_URL and temporarily override it
    old_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url

    try:
        # Get path to alembic.ini (it's in the backend directory)
        backend_dir = Path(__file__).parent.parent
        alembic_ini_path = backend_dir / "alembic.ini"

        # Create Alembic config and set the database URL
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
    finally:
        # Restore the original DATABASE_URL
        if old_database_url is not None:
            os.environ["DATABASE_URL"] = old_database_url
        else:
            os.environ.pop("DATABASE_URL", None)


def drop_all_tables(engine):
    """Drop all tables in the database."""
    SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine for the entire test session."""
    test_engine = create_engine(TEST_DATABASE_URL, echo=False)

    # Drop all tables first to ensure clean state
    drop_all_tables(test_engine)

    # Run migrations to create all tables
    run_migrations(TEST_DATABASE_URL)

    yield test_engine

    # Drop all tables at the end of the test session
    drop_all_tables(test_engine)
    test_engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for each test function.

    This fixture:
    - Creates a new session for each test
    - Cleans up all data after each test
    - Ensures tests are isolated from each other
    """
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=Session
    )
    session = SessionLocal()

    yield session

    # Clean up after the test
    session.close()

    # Clear all data from tables
    with engine.begin() as connection:
        # Delete in order to respect foreign key constraints
        connection.execute(album_photos.delete())
        for table in [PhotoMetadata, Version, Photo, Album, Library, User]:
            connection.execute(table.__table__.delete())


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up override
    app.dependency_overrides.clear()


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_fixture_path(fixtures_dir):
    """Return a sample fixture file path."""
    return fixtures_dir / "sample.json"


@pytest.fixture
def test_user(db_session):
    """Create a test user for authentication tests."""
    from app.auth import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        name="Test User",
        is_active=True,
        is_superuser=False,
        date_joined=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(client):
    """Create a user and return an authentication token."""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    # Login and get token
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpassword123"},
    )
    return response.json()["access_token"]
