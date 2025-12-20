"""Integration tests for photo metadata API endpoints"""

import json
from datetime import datetime
import uuid

import pytest


class TestPhotoMetadataAPI:
    """Test photo metadata handling in API endpoints"""

    def test_create_photo_with_metadata(self, client, auth_token):
        """Test creating a photo with metadata entries"""
        photo_uuid = str(uuid.uuid4())
        
        photo_data = {
            "uuid": photo_uuid,
            "original_filename": "test.jpg",
            "date": datetime.utcnow().isoformat(),
            "metadata": [
                {"key": "camera", "value": {"value": "Canon"}, "source": "macos"},
                {"key": "year", "value": {"value": "2024"}, "source": "macos"},
            ],
        }
        
        response = client.post(
            "/api/photos/",
            json=photo_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["uuid"] == photo_uuid
        assert data["metadata"] is not None
        assert len(data["metadata"]) == 2

    def test_create_photo_with_search_info_converts_to_metadata(self, client, auth_token):
        """Test that search_info is converted to metadata on create"""
        photo_uuid = str(uuid.uuid4())
        
        photo_data = {
            "uuid": photo_uuid,
            "original_filename": "test.jpg",
            "date": datetime.utcnow().isoformat(),
            "search_info": {
                "camera": "Canon",
                "year": "2024",
                "labels": ["Wedding", "People"],
            },
        }
        
        response = client.post(
            "/api/photos/",
            json=photo_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["uuid"] == photo_uuid
        # search_info should have been converted to metadata
        assert data["metadata"] is not None
        assert len(data["metadata"]) == 3
        
        # Check that source is set to "legacy" for search_info conversion
        assert all(m["source"] == "legacy" for m in data["metadata"])

    def test_update_photo_extends_metadata(self, client, auth_token):
        """Test that PATCH extends metadata rather than replacing it"""
        photo_uuid = str(uuid.uuid4())
        
        # Create photo with initial metadata
        photo_data = {
            "uuid": photo_uuid,
            "original_filename": "test.jpg",
            "date": datetime.utcnow().isoformat(),
            "metadata": [
                {"key": "camera", "value": {"value": "Canon"}, "source": "macos"},
                {"key": "year", "value": {"value": "2024"}, "source": "macos"},
            ],
        }
        
        response = client.post(
            "/api/photos/",
            json=photo_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        
        # Update photo with additional metadata
        update_data = {
            "metadata": [
                {"key": "season", "value": {"value": "Winter"}, "source": "macos"},
            ],
        }
        
        response = client.patch(
            f"/api/photos/{photo_uuid}/",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have all 3 metadata entries (2 original + 1 new)
        assert len(data["metadata"]) == 3
        assert any(m["key"] == "camera" for m in data["metadata"])
        assert any(m["key"] == "year" for m in data["metadata"])
        assert any(m["key"] == "season" for m in data["metadata"])

    def test_update_photo_updates_existing_metadata_by_key_and_source(self, client, auth_token):
        """Test that PATCH updates existing metadata with same key (unique constraint on photo_uuid, key)"""
        photo_uuid = str(uuid.uuid4())
        
        # Create photo with initial metadata
        photo_data = {
            "uuid": photo_uuid,
            "original_filename": "test.jpg",
            "date": datetime.utcnow().isoformat(),
            "metadata": [
                {"key": "camera", "value": {"value": "Canon"}, "source": "macos"},
            ],
        }
        
        response = client.post(
            "/api/photos/",
            json=photo_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        
        # Update metadata with same key but different value and source
        update_data = {
            "metadata": [
                {"key": "camera", "value": {"value": "Nikon"}, "source": "exif"},
            ],
        }
        
        response = client.patch(
            f"/api/photos/{photo_uuid}/",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still have only 1 metadata entry (unique constraint on photo_uuid, key)
        # The value and source should be updated
        assert len(data["metadata"]) == 1
        assert data["metadata"][0]["key"] == "camera"
        assert data["metadata"][0]["value"] == {"value": "Nikon"}
        assert data["metadata"][0]["source"] == "exif"

    def test_batch_create_with_search_info_converts_to_metadata(self, client, auth_token):
        """Test that batch create converts search_info to metadata"""
        photo_uuid1 = str(uuid.uuid4())
        photo_uuid2 = str(uuid.uuid4())
        
        batch_data = {
            "photos": [
                {
                    "uuid": photo_uuid1,
                    "original_filename": "test1.jpg",
                    "date": datetime.utcnow().isoformat(),
                    "search_info": {
                        "camera": "Canon",
                        "year": "2024",
                    },
                },
                {
                    "uuid": photo_uuid2,
                    "original_filename": "test2.jpg",
                    "date": datetime.utcnow().isoformat(),
                    "metadata": [
                        {"key": "camera", "value": {"value": "Nikon"}, "source": "macos"},
                    ],
                },
            ],
        }
        
        response = client.post(
            "/api/photos/batch/",
            json=batch_data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 2
        assert data["errors"] == 0
        
        # Verify first photo has metadata from search_info
        response1 = client.get(
            f"/api/photos/{photo_uuid1}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response1.status_code == 200
        photo1_data = response1.json()
        assert len(photo1_data["metadata"]) == 2
        assert all(m["source"] == "legacy" for m in photo1_data["metadata"])
        
        # Verify second photo has explicit metadata
        response2 = client.get(
            f"/api/photos/{photo_uuid2}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response2.status_code == 200
        photo2_data = response2.json()
        assert len(photo2_data["metadata"]) == 1
        assert photo2_data["metadata"][0]["source"] == "macos"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
