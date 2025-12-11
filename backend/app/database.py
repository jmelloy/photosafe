"""Database configuration"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

# Get database URL from environment variable (PostgreSQL required)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://photosafe:photosafe@localhost:5432/photosafe"
)

# Create engine for PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
