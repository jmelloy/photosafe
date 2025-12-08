"""Tests for CLI commands"""

import pytest
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile
import json
import os

from app.database import Base, get_db
from app.models import User, Library, Photo
from cli.user_commands import user
from cli.library_commands import library
from cli.import_commands import import_photos


# NOTE: These tests require a PostgreSQL test database
# Test database setup - PostgreSQL connection required
# For local testing, set up a test database: createdb photosafe_test
# Then set: export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/photosafe_test"
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://photosafe:photosafe@localhost:5432/photosafe_test")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    
    # Override get_db for CLI commands
    from cli import user_commands, library_commands, import_commands
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Patch SessionLocal in all CLI modules
    user_commands.SessionLocal = TestingSessionLocal
    library_commands.SessionLocal = TestingSessionLocal
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
def runner():
    """Click CLI runner"""
    return CliRunner()


class TestUserCommands:
    """Test user CLI commands"""
    
    def test_create_user(self, setup_database, runner):
        """Test creating a user"""
        result = runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123',
            '--name', 'Test User'
        ])
        
        assert result.exit_code == 0
        assert 'User created successfully' in result.output
        assert 'testuser' in result.output
        
        # Verify in database
        db = TestingSessionLocal()
        try:
            db_user = db.query(User).filter(User.username == 'testuser').first()
            assert db_user is not None
            assert db_user.email == 'test@example.com'
            assert db_user.name == 'Test User'
        finally:
            db.close()
    
    def test_create_superuser(self, setup_database, runner):
        """Test creating a superuser"""
        result = runner.invoke(user, [
            'create',
            '--username', 'admin',
            '--email', 'admin@example.com',
            '--password', 'adminpass123',
            '--superuser'
        ])
        
        assert result.exit_code == 0
        assert 'Superuser privileges granted' in result.output
        
        # Verify in database
        db = TestingSessionLocal()
        try:
            db_user = db.query(User).filter(User.username == 'admin').first()
            assert db_user.is_superuser is True
        finally:
            db.close()
    
    def test_create_duplicate_user(self, setup_database, runner):
        """Test creating a duplicate user"""
        # Create first user
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        # Try to create duplicate
        result = runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'different@example.com',
            '--password', 'testpass123'
        ])
        
        assert result.exit_code == 0  # Click doesn't return error code by default
        assert 'already exists' in result.output
    
    def test_list_users(self, setup_database, runner):
        """Test listing users"""
        # Create test users
        runner.invoke(user, [
            'create',
            '--username', 'user1',
            '--email', 'user1@example.com',
            '--password', 'pass123'
        ])
        runner.invoke(user, [
            'create',
            '--username', 'user2',
            '--email', 'user2@example.com',
            '--password', 'pass123'
        ])
        
        result = runner.invoke(user, ['list'])
        
        assert result.exit_code == 0
        assert 'user1' in result.output
        assert 'user2' in result.output
    
    def test_user_info(self, setup_database, runner):
        """Test getting user info"""
        # Create test user
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123',
            '--name', 'Test User'
        ])
        
        result = runner.invoke(user, ['info', 'testuser'])
        
        assert result.exit_code == 0
        assert 'Test User' in result.output
        assert 'test@example.com' in result.output


class TestLibraryCommands:
    """Test library CLI commands"""
    
    def test_create_library(self, setup_database, runner):
        """Test creating a library"""
        # Create user first
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        # Create library
        result = runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'My Photos',
            '--path', '/home/testuser/photos',
            '--description', 'Test library'
        ])
        
        assert result.exit_code == 0
        assert 'Library created successfully' in result.output
        assert 'My Photos' in result.output
        
        # Verify in database
        db = TestingSessionLocal()
        try:
            db_library = db.query(Library).filter(Library.name == 'My Photos').first()
            assert db_library is not None
            assert db_library.path == '/home/testuser/photos'
            assert db_library.description == 'Test library'
        finally:
            db.close()
    
    def test_list_libraries(self, setup_database, runner):
        """Test listing libraries"""
        # Create user and libraries
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'Library 1',
            '--path', '/path1'
        ])
        runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'Library 2',
            '--path', '/path2'
        ])
        
        result = runner.invoke(library, ['list'])
        
        assert result.exit_code == 0
        assert 'Library 1' in result.output
        assert 'Library 2' in result.output
    
    def test_library_info(self, setup_database, runner):
        """Test getting library info"""
        # Create user and library
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        result = runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'My Photos',
            '--path', '/home/testuser/photos'
        ])
        
        result = runner.invoke(library, ['info', '1'])
        
        assert result.exit_code == 0
        assert 'My Photos' in result.output
        assert '/home/testuser/photos' in result.output


class TestImportCommands:
    """Test import CLI commands"""
    
    def test_import_with_sidecar(self, setup_database, runner):
        """Test importing photos with JSON sidecar"""
        # Create user and library
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'Test Library'
        ])
        
        # Create temporary test folder with photo and sidecar
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test image
            test_image = tmpdir / "test.jpg"
            test_image.write_text("test image data")
            
            # Create sidecar JSON
            sidecar = tmpdir / "test.json"
            sidecar_data = {
                "uuid": "TEST-UUID-1234",
                "fingerprint": "test-fingerprint",
                "original_filename": "test.jpg",
                "date": "2024-01-01T12:00:00-08:00",
                "title": "Test Photo",
                "description": "A test photo",
                "keywords": ["test", "sample"],
                "favorite": True,
                "isphoto": True,
                "width": 1920,
                "height": 1080
            }
            sidecar.write_text(json.dumps(sidecar_data))
            
            # Import photos
            result = runner.invoke(import_photos, [
                '--username', 'testuser',
                '--library-id', '1',
                '--folder', str(tmpdir),
                '--sidecar-format', 'json'
            ])
            
            assert result.exit_code == 0
            assert 'Import complete' in result.output
            assert 'Imported: 1' in result.output
            
            # Verify in database
            db = TestingSessionLocal()
            try:
                photo = db.query(Photo).filter(Photo.uuid == 'TEST-UUID-1234').first()
                assert photo is not None
                assert photo.title == 'Test Photo'
                assert photo.library_id == 1
            finally:
                db.close()
    
    def test_import_dry_run(self, setup_database, runner):
        """Test import with dry-run flag"""
        # Create user and library
        runner.invoke(user, [
            'create',
            '--username', 'testuser',
            '--email', 'test@example.com',
            '--password', 'testpass123'
        ])
        
        runner.invoke(library, [
            'create',
            '--username', 'testuser',
            '--name', 'Test Library'
        ])
        
        # Create temporary test folder
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_image = tmpdir / "test.jpg"
            test_image.write_text("test image data")
            
            # Import with dry run
            result = runner.invoke(import_photos, [
                '--username', 'testuser',
                '--library-id', '1',
                '--folder', str(tmpdir),
                '--dry-run'
            ])
            
            assert result.exit_code == 0
            assert 'Dry run - no changes made' in result.output
            
            # Verify nothing was imported
            db = TestingSessionLocal()
            try:
                count = db.query(Photo).count()
                assert count == 0
            finally:
                db.close()
