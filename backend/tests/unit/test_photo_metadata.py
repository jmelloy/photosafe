"""Tests for photo metadata functionality"""

import json
from datetime import datetime
import uuid

import pytest

from app.models import Photo, PhotoMetadata, User
from app.utils import (
    process_search_info_to_metadata,
    extend_photo_metadata,
)


class TestPhotoMetadata:
    """Test PhotoMetadata model and utility functions"""

    def test_process_search_info_to_metadata_basic(self):
        """Test converting search_info dictionary to metadata entries"""
        search_info = {
            "camera": "Canon PowerShot A590 IS",
            "year": "1980",
            "season": "Winter",
            "month": "January",
        }
        
        metadata = process_search_info_to_metadata(search_info, source="macos")
        
        assert len(metadata) == 4
        assert all(m["source"] == "macos" for m in metadata)
        assert any(m["key"] == "camera" and m["value"] == "Canon PowerShot A590 IS" for m in metadata)
        assert any(m["key"] == "year" and m["value"] == "1980" for m in metadata)

    def test_process_search_info_to_metadata_with_lists(self):
        """Test converting search_info with list values"""
        search_info = {
            "labels": ["Wedding", "People", "Outdoor"],
            "activities": ["Celebration", "Holiday"],
        }
        
        metadata = process_search_info_to_metadata(search_info, source="macos")
        
        assert len(metadata) == 2
        
        # Check that lists are JSON encoded
        labels_entry = next(m for m in metadata if m["key"] == "labels")
        assert json.loads(labels_entry["value"]) == ["Wedding", "People", "Outdoor"]

    def test_process_search_info_to_metadata_skips_empty(self):
        """Test that empty values are skipped"""
        search_info = {
            "camera": "Canon",
            "empty_list": [],
            "empty_dict": {},
            "none_value": None,
            "empty_string": "",
        }
        
        metadata = process_search_info_to_metadata(search_info, source="macos")
        
        # Should only include camera and empty_string (empty string is not skipped)
        assert len(metadata) == 2
        assert any(m["key"] == "camera" for m in metadata)
        assert any(m["key"] == "empty_string" for m in metadata)

    def test_extend_photo_metadata_new_entries(self, db_session):
        """Test adding new metadata entries to a photo"""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            date_joined=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.flush()
        
        # Create a test photo
        photo_uuid = uuid.uuid4()
        photo = Photo(
            uuid=photo_uuid,
            original_filename="test.jpg",
            date=datetime.utcnow(),
            owner_id=user.id,
        )
        db_session.add(photo)
        db_session.flush()
        
        # Add metadata entries
        metadata_entries = [
            {"key": "camera", "value": "Canon", "source": "macos"},
            {"key": "year", "value": "2024", "source": "macos"},
        ]
        
        extend_photo_metadata(photo, metadata_entries, db_session)
        db_session.commit()
        
        # Query metadata
        metadata = db_session.query(PhotoMetadata).filter(
            PhotoMetadata.photo_uuid == photo_uuid
        ).all()
        
        assert len(metadata) == 2
        assert any(m.key == "camera" and m.value == "Canon" for m in metadata)
        assert any(m.key == "year" and m.value == "2024" for m in metadata)

    def test_extend_photo_metadata_updates_existing(self, db_session):
        """Test that existing metadata with same key+source is updated"""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            date_joined=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.flush()
        
        # Create a test photo
        photo_uuid = uuid.uuid4()
        photo = Photo(
            uuid=photo_uuid,
            original_filename="test.jpg",
            date=datetime.utcnow(),
            owner_id=user.id,
        )
        db_session.add(photo)
        db_session.flush()
        
        # Add initial metadata
        initial_metadata = PhotoMetadata(
            photo_uuid=photo_uuid,
            key="camera",
            value="Canon",
            source="macos",
        )
        db_session.add(initial_metadata)
        db_session.commit()
        
        # Update with new value
        metadata_entries = [
            {"key": "camera", "value": "Nikon", "source": "macos"},
        ]
        
        extend_photo_metadata(photo, metadata_entries, db_session)
        db_session.commit()
        
        # Query metadata
        metadata = db_session.query(PhotoMetadata).filter(
            PhotoMetadata.photo_uuid == photo_uuid
        ).all()
        
        # Should still have only 1 entry, but with updated value
        assert len(metadata) == 1
        assert metadata[0].key == "camera"
        assert metadata[0].value == "Nikon"
        assert metadata[0].source == "macos"

    def test_extend_photo_metadata_different_sources(self, db_session):
        """Test that different sources create separate entries for same key"""
        # Create a test user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            date_joined=datetime.utcnow(),
        )
        db_session.add(user)
        db_session.flush()
        
        # Create a test photo
        photo_uuid = uuid.uuid4()
        photo = Photo(
            uuid=photo_uuid,
            original_filename="test.jpg",
            date=datetime.utcnow(),
            owner_id=user.id,
        )
        db_session.add(photo)
        db_session.flush()
        
        # Add metadata from macos source
        metadata_entries_macos = [
            {"key": "camera", "value": "Canon", "source": "macos"},
        ]
        extend_photo_metadata(photo, metadata_entries_macos, db_session)
        db_session.commit()
        
        # Add metadata from different source with same key
        metadata_entries_exif = [
            {"key": "camera", "value": "Canon EOS", "source": "exif"},
        ]
        extend_photo_metadata(photo, metadata_entries_exif, db_session)
        db_session.commit()
        
        # Query metadata
        metadata = db_session.query(PhotoMetadata).filter(
            PhotoMetadata.photo_uuid == photo_uuid
        ).all()
        
        # Should have 2 entries with same key but different sources
        assert len(metadata) == 2
        macos_entry = next(m for m in metadata if m.source == "macos")
        exif_entry = next(m for m in metadata if m.source == "exif")
        
        assert macos_entry.value == "Canon"
        assert exif_entry.value == "Canon EOS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
