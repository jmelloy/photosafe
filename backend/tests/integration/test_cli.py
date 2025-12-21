"""Tests for CLI commands"""

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from click.testing import CliRunner
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from app.models import Album, Library, Photo, User, Version, album_photos
from cli.import_commands import import_photos
from cli.library_commands import library
from cli.user_commands import user


class TestUserCommands:
    """Test user CLI commands"""

    def test_create_user(self, db_session, runner):
        """Test creating a user"""
        username, email, *rest = str(uuid.uuid4()).split("-")

        result = runner.invoke(
            user,
            [
                "create",
                "--username",
                username,
                "--email",
                f"{email}@example.com",
                "--password",
                "testpass123",
                "--name",
                "Test User",
            ],
        )

        assert result.exit_code == 0
        assert "User created successfully" in result.output
        assert username in result.output

        # Close the current transaction and start a new one to see committed data
        db_session.rollback()
        db_user = db_session.exec(
            select(User).where(User.username == username)
        ).scalar_one()
        print(db_user)
        assert db_user is not None
        assert db_user.email == f"{email}@example.com"
        assert db_user.name == "Test User"

    def test_create_duplicate_user(self, runner):
        """Test creating a duplicate user"""
        # Create first user
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "testuser",
                "--email",
                "test@example.com",
                "--password",
                "testpass123",
            ],
        )

        # Try to create duplicate
        result = runner.invoke(
            user,
            [
                "create",
                "--username",
                "testuser",
                "--email",
                "different@example.com",
                "--password",
                "testpass123",
            ],
        )

        assert result.exit_code == 0  # Click doesn't return error code by default
        assert "already exists" in result.output

    def test_list_users(self, db_session, runner):
        """Test listing users"""
        # Create test users
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "user1",
                "--email",
                "user1@example.com",
                "--password",
                "pass123",
            ],
        )
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "user2",
                "--email",
                "user2@example.com",
                "--password",
                "pass123",
            ],
        )

        result = runner.invoke(user, ["list"])

        assert result.exit_code == 0
        assert "user1" in result.output
        assert "user2" in result.output

    def test_user_info(self, db_session, runner):
        """Test getting user info"""
        username, email = (
            str(uuid.uuid4()).split("-")[0],
            str(uuid.uuid4()).split("-")[0] + "@example.com",
        )
        # Create test user
        runner.invoke(
            user,
            [
                "create",
                "--username",
                username,
                "--email",
                email,
                "--password",
                "testpass123",
                "--name",
                "Test User",
            ],
        )

        result = runner.invoke(user, ["info", username])

        assert result.exit_code == 0
        assert "Test User" in result.output
        assert email in result.output


class TestLibraryCommands:
    """Test library CLI commands"""

    def test_create_library(self, db_session, runner):
        """Test creating a library"""

        username, email = (
            str(uuid.uuid4()).split("-")[0],
            str(uuid.uuid4()).split("-")[0] + "@example.com",
        )

        # Create user first
        runner.invoke(
            user,
            [
                "create",
                "--username",
                username,
                "--email",
                email,
                "--password",
                "testpass123",
            ],
        )

        # Create library
        result = runner.invoke(
            library,
            [
                "create",
                "--username",
                username,
                "--name",
                "My Photos",
                "--path",
                "/home/testuser/photos",
                "--description",
                "Test library",
            ],
        )

        assert result.exit_code == 0
        assert "Library created successfully" in result.output
        assert "My Photos" in result.output

        # Close the current transaction and start a new one to see committed data
        db_session.rollback()
        # Verify in database
        db_library = db_session.exec(
            select(Library).where(Library.name == "My Photos")
        ).scalar_one()
        assert db_library is not None
        assert db_library.path == "/home/testuser/photos"
        assert db_library.description == "Test library"

    def test_list_libraries(self, runner):
        """Test listing libraries"""
        # Create user and libraries
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "testuser",
                "--email",
                "test@example.com",
                "--password",
                "testpass123",
            ],
        )

        runner.invoke(
            library,
            [
                "create",
                "--username",
                "testuser",
                "--name",
                "Library 1",
                "--path",
                "/path1",
            ],
        )
        runner.invoke(
            library,
            [
                "create",
                "--username",
                "testuser",
                "--name",
                "Library 2",
                "--path",
                "/path2",
            ],
        )

        result = runner.invoke(library, ["list"])

        assert result.exit_code == 0
        assert "Library 1" in result.output
        assert "Library 2" in result.output

    def test_library_info(self, runner):
        """Test getting library info"""
        # Create user and library
        username, email, library_name, *_ = str(uuid.uuid4()).split("-")
        runner.invoke(
            user,
            [
                "create",
                "--username",
                username,
                "--email",
                f"{email}",
                "--password",
                "testpass123",
            ],
        )

        create_result = runner.invoke(
            library,
            [
                "create",
                "--username",
                username,
                "--name",
                library_name,
                "--path",
                "/home/testuser/photos",
            ],
        )

        # Extract library ID from output: "✓ Library created successfully: {name} (ID: {id})"
        import re

        match = re.search(r"\(ID: (\d+)\)", create_result.output)
        assert match, f"Could not find library ID in output: {create_result.output}"
        library_id = match.group(1)

        result = runner.invoke(library, ["info", library_id])

        assert result.exit_code == 0
        assert library_name in result.output
        assert "/home/testuser/photos" in result.output


class TestImportCommands:
    """Test import CLI commands"""

    def test_import_with_sidecar(self, db_session, runner):
        """Test importing photos with JSON sidecar"""
        # Create user and library
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "testuser",
                "--email",
                "test@example.com",
                "--password",
                "testpass123",
            ],
        )

        runner.invoke(
            library, ["create", "--username", "testuser", "--name", "Test Library"]
        )

        # Create temporary test folder with photo and sidecar
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test image
            test_image = tmpdir / "test.jpg"
            test_image.write_text("test image data")

            # Create sidecar JSON
            test_uuid = str(uuid.uuid4())
            sidecar = tmpdir / "test.json"
            sidecar_data = {
                "uuid": test_uuid,
                "fingerprint": "test-fingerprint",
                "original_filename": "test.jpg",
                "date": "2024-01-01T12:00:00-08:00",
                "title": "Test Photo",
                "description": "A test photo",
                "keywords": ["test", "sample"],
                "favorite": True,
                "isphoto": True,
                "width": 1920,
                "height": 1080,
            }
            sidecar.write_text(json.dumps(sidecar_data))

            # Import photos
            result = runner.invoke(
                import_photos,
                [
                    "--username",
                    "testuser",
                    "--library-id",
                    "1",
                    "--folder",
                    str(tmpdir),
                    "--sidecar-format",
                    "json",
                ],
            )

            assert result.exit_code == 0
            assert "Import complete" in result.output
            assert "Imported: 1" in result.output

            # Close the current transaction and start a new one to see committed data
            db_session.rollback()
            # Verify in database
            photo = db_session.exec(
                select(Photo).where(Photo.uuid == test_uuid)
            ).scalar_one()
            assert photo is not None
            assert photo.title == "Test Photo"
            assert photo.library_id == 1

    def test_import_dry_run(self, db_session, runner):
        """Test import with dry-run flag"""
        # Create user and library
        runner.invoke(
            user,
            [
                "create",
                "--username",
                "testuser",
                "--email",
                "test@example.com",
                "--password",
                "testpass123",
            ],
        )

        runner.invoke(
            library, ["create", "--username", "testuser", "--name", "Test Library"]
        )

        # Create temporary test folder
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_image = tmpdir / "test.jpg"
            test_image.write_text("test image data")

            # Import with dry run
            result = runner.invoke(
                import_photos,
                [
                    "--username",
                    "testuser",
                    "--library-id",
                    "1",
                    "--folder",
                    str(tmpdir),
                    "--dry-run",
                ],
            )

            assert result.exit_code == 0
            assert "Dry run - no changes made" in result.output

            # Verify nothing was imported
            count = len(db_session.exec(select(Photo)).all())
            assert count == 0
