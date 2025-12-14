"""Database configuration"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

# Get database URL from environment variable (PostgreSQL required)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://photosafe:photosafe@localhost:5432/photosafe"
)

# Enable SQL debug logging if DEBUG environment variable is set
DEBUG_SQL = os.getenv("DEBUG_SQL", "false").lower() in ("true", "1", "yes")

# Create engine for PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=DEBUG_SQL)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=Session
)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
