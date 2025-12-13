"""Test to verify indexes are created correctly on photos table"""

import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlmodel import Session, SQLModel

# Test database setup - PostgreSQL connection required
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5432/photosafe_test",
)


def test_photos_indexes_exist():
    """Test that all expected indexes exist on the photos table"""
    # Skip test if no database is available
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        inspector = inspect(engine)
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
    
    # Get indexes for photos table
    indexes = inspector.get_indexes("photos")
    index_names = {idx["name"] for idx in indexes}
    
    # Expected indexes from the migration
    expected_indexes = {
        "ix_photos_owner_id",
        "ix_photos_library_id",
        "ix_photos_date",
        "ix_photos_albums_gin",
        "ix_photos_keywords_gin",
        "ix_photos_persons_gin",
        "ix_photos_master_fingerprint",
        "ix_photos_favorite",
        "ix_photos_isphoto",
        "ix_photos_ismovie",
        "ix_photos_screenshot",
        "ix_photos_panorama",
        "ix_photos_portrait",
        "ix_photos_location",
    }
    
    # Verify all expected indexes are present
    missing_indexes = expected_indexes - index_names
    
    if missing_indexes:
        print(f"\nMissing indexes: {missing_indexes}")
        print(f"Existing indexes: {index_names}")
        pytest.fail(f"Missing indexes: {missing_indexes}")
    
    print(f"\n✅ All {len(expected_indexes)} expected indexes are present on photos table")
    
    # Verify GIN indexes are using GIN method
    for idx in indexes:
        if "gin" in idx["name"]:
            # The index info doesn't directly show the method, but we can verify it exists
            print(f"  - {idx['name']}: columns={idx['column_names']}")


def test_index_columns():
    """Test that indexes are on the correct columns"""
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        inspector = inspect(engine)
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
    
    indexes = inspector.get_indexes("photos")
    index_columns = {idx["name"]: idx["column_names"] for idx in indexes}
    
    # Verify specific indexes have correct columns
    expected_columns = {
        "ix_photos_owner_id": ["owner_id"],
        "ix_photos_library_id": ["library_id"],
        "ix_photos_date": ["date"],
        "ix_photos_albums_gin": ["albums"],
        "ix_photos_keywords_gin": ["keywords"],
        "ix_photos_persons_gin": ["persons"],
        "ix_photos_master_fingerprint": ["masterFingerprint"],
        "ix_photos_favorite": ["favorite"],
        "ix_photos_isphoto": ["isphoto"],
        "ix_photos_ismovie": ["ismovie"],
        "ix_photos_screenshot": ["screenshot"],
        "ix_photos_panorama": ["panorama"],
        "ix_photos_portrait": ["portrait"],
        "ix_photos_location": ["latitude", "longitude"],
    }
    
    for index_name, expected_cols in expected_columns.items():
        if index_name in index_columns:
            actual_cols = index_columns[index_name]
            assert actual_cols == expected_cols, (
                f"Index {index_name} has columns {actual_cols}, "
                f"expected {expected_cols}"
            )
            print(f"✅ {index_name}: {actual_cols}")
        else:
            pytest.fail(f"Index {index_name} not found")


if __name__ == "__main__":
    # Run tests directly
    print("Testing photos table indexes...")
    print("=" * 60)
    
    try:
        test_photos_indexes_exist()
        test_index_columns()
        print("\n" + "=" * 60)
        print("✅ All index tests passed!")
    except pytest.skip.Exception as e:
        print(f"\n⚠️  Tests skipped: {e}")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        raise
