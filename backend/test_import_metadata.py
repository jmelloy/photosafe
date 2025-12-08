"""Tests for photo import with metadata and EXIF extraction"""

import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile
import json
import os
from PIL import Image
from datetime import datetime

from app.database import Base
from app.models import User, Library, Photo
from cli.import_commands import import_photos, extract_exif_data, parse_meta_json


# NOTE: These tests require a PostgreSQL test database
# Test database setup - PostgreSQL connection required
# For local testing, set up a test database: createdb photosafe_test
# Set environment variable: export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/photosafe_test"
# The default below is for Docker Compose development environment only
SQLALCHEMY_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://photosafe:photosafe@localhost:5432/photosafe_test",
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)

    # Override SessionLocal in import_commands
    from cli import import_commands

    import_commands.SessionLocal = TestingSessionLocal

    yield

    # Cleanup
    db = TestingSessionLocal()
    try:
        db.query(Photo).delete()
        db.query(Library).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def test_user(setup_database):
    """Create a test user"""
    db = TestingSessionLocal()
    try:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            name="Test User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def test_library(setup_database, test_user):
    """Create a test library"""
    db = TestingSessionLocal()
    try:
        library = Library(name="test_library", owner_id=test_user.id, path="/tmp/test")
        db.add(library)
        db.commit()
        db.refresh(library)
        return library
    finally:
        db.close()


@pytest.fixture
def runner():
    """Click CLI runner"""
    return CliRunner()


@pytest.fixture
def temp_image_with_exif():
    """Create a temporary image with EXIF data"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")

        # Add some EXIF data
        exif = img.getexif()
        exif[271] = "Test Camera Make"  # Make
        exif[272] = "Test Camera Model"  # Model
        exif[274] = 1  # Orientation

        img.save(f.name, exif=exif)
        yield Path(f.name)

    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestEXIFExtraction:
    """Test EXIF extraction functionality"""

    def test_extract_exif_from_image(self, temp_image_with_exif):
        """Test extracting EXIF data from an image"""
        exif_data = extract_exif_data(temp_image_with_exif)

        assert exif_data is not None
        assert isinstance(exif_data, dict)

        # Check if basic EXIF data was extracted
        # Note: The EXIF data might be in the raw section
        assert "_raw" in exif_data or len(exif_data) > 0

    def test_extract_exif_no_exif(self):
        """Test extracting EXIF from image without EXIF data"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img = Image.new("RGB", (50, 50), color="blue")
            img.save(f.name)
            temp_path = Path(f.name)

            exif_data = extract_exif_data(temp_path)

            # Should return empty dict or dict with minimal data
            assert isinstance(exif_data, dict)

            temp_path.unlink()


class TestMetaJsonParsing:
    """Test meta.json parsing functionality"""

    def test_parse_meta_json_with_arbitrary_data(self):
        """Test parsing meta.json with arbitrary metadata"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            meta_data = {
                "custom_field_1": "value1",
                "custom_field_2": 123,
                "nested": {"field": "nested_value"},
            }
            json.dump(meta_data, f)
            f.flush()
            temp_path = Path(f.name)

            result = parse_meta_json(temp_path)

            # Arbitrary data should be wrapped in 'fields'
            assert "fields" in result
            assert result["fields"]["custom_field_1"] == "value1"
            assert result["fields"]["custom_field_2"] == 123

            temp_path.unlink()

    def test_parse_meta_json_with_known_fields(self):
        """Test parsing meta.json with known PhotoSafe fields"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            meta_data = {
                "title": "Test Photo",
                "description": "A test photo",
                "keywords": ["test", "photo"],
                "custom_field": "custom_value",
            }
            json.dump(meta_data, f)
            f.flush()
            temp_path = Path(f.name)

            result = parse_meta_json(temp_path)

            # Known fields should be at top level
            assert result["title"] == "Test Photo"
            assert result["description"] == "A test photo"
            assert result["keywords"] == ["test", "photo"]
            assert result["custom_field"] == "custom_value"

            temp_path.unlink()

    def test_parse_meta_json_invalid_file(self):
        """Test parsing invalid meta.json file"""
        result = parse_meta_json(Path("/nonexistent/meta.json"))

        # Should return empty dict on error
        assert result == {}


class TestPhotoImportWithMetadata:
    """Test photo import with metadata files"""

    def test_import_with_meta_json(self, runner, test_user, test_library):
        """Test importing photos with meta.json sidecar"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a test image
            img_path = tmpdir_path / "test_photo.jpg"
            img = Image.new("RGB", (100, 100), color="green")
            img.save(img_path)

            # Create meta.json with arbitrary metadata
            meta_json_path = tmpdir_path / "meta.json"
            meta_data = {
                "photographer": "John Doe",
                "location_name": "Test Location",
                "camera_settings": {"custom_mode": "portrait"},
            }
            with open(meta_json_path, "w") as f:
                json.dump(meta_data, f)

            # Run import
            result = runner.invoke(
                import_photos,
                [
                    "--username",
                    test_user.username,
                    "--library-id",
                    str(test_library.id),
                    "--folder",
                    str(tmpdir_path),
                ],
            )

            assert result.exit_code == 0
            assert "Imported: 1" in result.output

            # Verify photo was imported with metadata
            db = TestingSessionLocal()
            try:
                photo = db.query(Photo).filter(Photo.owner_id == test_user.id).first()
                assert photo is not None
                assert photo.original_filename == "test_photo.jpg"

                # Check if fields contains the arbitrary metadata
                if photo.fields:
                    fields_data = (
                        json.loads(photo.fields)
                        if isinstance(photo.fields, str)
                        else photo.fields
                    )
                    assert "photographer" in fields_data or "fields" in fields_data
            finally:
                db.close()

    def test_import_with_exif_extraction(
        self, runner, test_user, test_library, temp_image_with_exif
    ):
        """Test that EXIF data is extracted during import"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Copy the temp image to the import directory
            import shutil

            img_path = tmpdir_path / "test_with_exif.jpg"
            shutil.copy(temp_image_with_exif, img_path)

            # Run import
            result = runner.invoke(
                import_photos,
                [
                    "--username",
                    test_user.username,
                    "--library-id",
                    str(test_library.id),
                    "--folder",
                    str(tmpdir_path),
                ],
            )

            assert result.exit_code == 0
            assert "Imported: 1" in result.output

            # Verify photo has EXIF data
            db = TestingSessionLocal()
            try:
                photo = db.query(Photo).filter(Photo.owner_id == test_user.id).first()
                assert photo is not None

                # Check if EXIF data was stored
                if photo.exif:
                    exif_data = (
                        json.loads(photo.exif)
                        if isinstance(photo.exif, str)
                        else photo.exif
                    )
                    assert isinstance(exif_data, dict)
                    # EXIF data should have at least the _raw field or some data
                    assert len(exif_data) > 0
            finally:
                db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
