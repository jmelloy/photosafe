# SQLModel Migration Guide

## Overview

This document describes the migration from pure SQLAlchemy + Pydantic to SQLModel, which combines both into a unified model definition.

## What is SQLModel?

SQLModel is a library that combines SQLAlchemy and Pydantic, allowing you to define models that work both as database tables and as Pydantic schemas. This eliminates code duplication and provides a cleaner, more maintainable codebase.

## Changes Made

### 1. Dependencies

Added SQLModel to `pyproject.toml`:
```toml
dependencies = [
    ...
    "sqlmodel>=0.0.22",
    ...
]
```

### 2. Database Configuration

Updated `app/database.py` to use SQLModel's Session:

**Before:**
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**After:**
```python
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
```

### 3. Model Definitions

Converted all models from SQLAlchemy to SQLModel:

**Before (SQLAlchemy):**
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    
    photos = relationship("Photo", back_populates="owner")
```

**After (SQLModel):**
```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(unique=True, index=True, nullable=False, sa_type=String)
    email: str = Field(unique=True, index=True, nullable=False, sa_type=String)
    
    photos: List["Photo"] = Relationship(back_populates="owner")
```

### 4. Key Patterns

#### Basic Fields
```python
# Simple field with default
name: str = Field(default="", sa_type=String)

# Optional field
description: Optional[str] = Field(default=None, sa_type=Text)

# Field with constraints
email: str = Field(unique=True, index=True, nullable=False, sa_type=String)
```

#### Primary Keys
```python
# Auto-incrementing integer primary key
id: Optional[int] = Field(default=None, primary_key=True, index=True)

# String primary key with default factory
uuid: str = Field(
    default_factory=lambda: str(uuid.uuid4()),
    primary_key=True,
    sa_type=String,
)
```

#### Foreign Keys
```python
owner_id: int = Field(foreign_key="users.id", nullable=False)
```

#### Relationships
```python
# One-to-many
photos: List["Photo"] = Relationship(back_populates="owner")

# Many-to-one
owner: Optional["User"] = Relationship(back_populates="photos")

# With cascade
versions: List["Version"] = Relationship(
    back_populates="photo", 
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
```

#### PostgreSQL-Specific Types

For PostgreSQL ARRAY and JSONB types, use `sa_column`:

```python
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

keywords: Optional[List[str]] = Field(
    default=None, 
    sa_column=Column(ARRAY(String), nullable=True)
)

exif: Optional[Dict[str, Any]] = Field(
    default=None, 
    sa_column=Column(JSONB, nullable=True)
)
```

### 5. Alembic Integration

Updated `alembic/env.py` to use SQLModel.metadata:

**Before:**
```python
from app.database import Base
target_metadata = Base.metadata
```

**After:**
```python
from sqlmodel import SQLModel
from app.models import User, Photo, Album, Version, Library
target_metadata = SQLModel.metadata
```

### 6. Test Files

Updated test files to use SQLModel:

**Before:**
```python
from sqlalchemy.orm import sessionmaker
from app.database import Base

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
```

**After:**
```python
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
SQLModel.metadata.create_all(bind=engine)
```

### 7. Schemas (Kept for Compatibility)

The `app/schemas.py` file is kept for:
- Response models with computed fields (e.g., `url` field in `PhotoResponse`)
- Update schemas with all optional fields
- Backward compatibility with existing API endpoints

## Benefits

1. **Reduced Code Duplication**: No need to define models twice (once in SQLAlchemy, once in Pydantic)
2. **Type Safety**: Full Python type hints work for both database and validation
3. **Automatic Validation**: Pydantic validation works automatically on model instances
4. **Simpler Syntax**: More Pythonic and easier to read
5. **Better IDE Support**: Type hints improve autocomplete and error detection

## Backward Compatibility

- All database tables remain unchanged
- Existing migrations work without modification
- API endpoints continue to work as before
- Schemas are kept for response models with additional computed fields

## Known Issues

### SQLite Tests
Tests using SQLite in-memory database (e.g., `test_filtering.py`, `test_blocks.py`) will fail because SQLite doesn't support PostgreSQL's ARRAY type. This is a pre-existing limitation, not a result of the SQLModel migration.

**Workaround**: Use PostgreSQL for all tests, or create SQLite-compatible test fixtures.

## Migration Checklist

If you're migrating other models to SQLModel, follow these steps:

1. Add `from sqlmodel import SQLModel, Field, Relationship` imports
2. Change class definition from `class Model(Base):` to `class Model(SQLModel, table=True):`
3. Convert `Column()` definitions to type hints with `Field()`
4. Update relationship definitions to use `Relationship()` instead of `relationship()`
5. For PostgreSQL-specific types (ARRAY, JSONB), use `sa_column=Column(...)`
6. Update any imports of `Base` to use `SQLModel.metadata` instead
7. Test the model can be imported and used

## References

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [SQLModel Tutorial](https://sqlmodel.tiangolo.com/tutorial/)
- [FastAPI with SQLModel](https://sqlmodel.tiangolo.com/tutorial/fastapi/)
