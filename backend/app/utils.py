"""Utility functions for photo processing"""

import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from .models import Photo, User, Library, VersionRead, PhotoRead, PhotoMetadata, PhotoMetadataRead


def serialize_json_field(value):
    """Convert list/dict to JSON string for storage"""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def deserialize_json_field(value):
    """Convert JSON string back to list/dict"""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


def serialize_photo_json_fields(photo_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize JSON fields in a photo dictionary for database storage

    Note: Only serializes JSONB fields (faces, place, exif, score, search_info, fields).
    Array fields (keywords, labels, albums, persons) are stored as PostgreSQL arrays
    and should NOT be JSON-serialized, as JSON serialization would convert them to
    character arrays (splitting each string into individual characters), breaking
    filtering functionality.

    Args:
        photo_dict: Dictionary of photo data to serialize

    Returns:
        Dictionary with JSONB fields serialized
    """
    # Only serialize JSONB fields - array fields should remain as lists
    jsonb_fields = [
        "faces",
        "place",
        "exif",
        "score",
        "search_info",
        "fields",
    ]
    for field in jsonb_fields:
        if field in photo_dict and photo_dict[field] is not None:
            photo_dict[field] = serialize_json_field(photo_dict[field])
    return photo_dict


def handle_library_upsert(library_name: str, current_user: User, db: Session) -> int:
    """Handle library name by upserting into libraries table.

    Looks up or creates a library with the given name for the current user.
    If the library doesn't exist, it will be created and flushed to the database.

    Args:
        library_name: The name of the library (should not be None or empty)
        current_user: The user who owns the library
        db: Database session

    Returns:
        The library_id for the given library name and user.

    Note:
        This function assumes library_name is not None or empty.
        Caller should validate before calling.
    """
    library = (
        db.query(Library)
        .filter(
            Library.owner_id == current_user.id,
            Library.name == library_name,
        )
        .first()
    )
    if not library:
        library = Library(
            name=library_name,
            owner_id=current_user.id,
        )
        db.add(library)
        db.flush()
    return library.id


def process_search_info_to_metadata(
    search_info: Dict[str, Any], source: str = "unknown"
) -> List[Dict[str, str]]:
    """Convert search_info dictionary to list of metadata entries.
    
    Args:
        search_info: Dictionary of search info data
        source: Source identifier for the metadata (e.g., "macos", "icloud")
    
    Returns:
        List of metadata dictionaries with key, value, and source
    """
    metadata_list = []
    
    if not search_info:
        return metadata_list
    
    for key, value in search_info.items():
        if value is None:
            continue
            
        # Handle list values by converting to JSON string
        if isinstance(value, list):
            if not value:  # Skip empty lists
                continue
            value_str = json.dumps(value)
        # Handle dict values by converting to JSON string
        elif isinstance(value, dict):
            if not value:  # Skip empty dicts
                continue
            value_str = json.dumps(value)
        # Handle other types
        else:
            value_str = str(value)
        
        metadata_list.append({
            "key": key,
            "value": value_str,
            "source": source,
        })
    
    return metadata_list


def extend_photo_metadata(
    photo: Photo, metadata_entries: List[Dict[str, str]], db: Session
) -> None:
    """Extend photo metadata with new entries, updating existing keys from the same source.
    
    Args:
        photo: Photo database model instance
        metadata_entries: List of metadata dictionaries with key, value, and source
        db: Database session
    """
    for entry in metadata_entries:
        # Check if metadata with this key and source already exists
        existing = (
            db.query(PhotoMetadata)
            .filter(
                PhotoMetadata.photo_uuid == photo.uuid,
                PhotoMetadata.key == entry["key"],
                PhotoMetadata.source == entry["source"],
            )
            .first()
        )
        
        if existing:
            # Update existing metadata
            existing.value = entry["value"]
        else:
            # Create new metadata entry
            new_metadata = PhotoMetadata(
                photo_uuid=photo.uuid,
                key=entry["key"],
                value=entry["value"],
                source=entry["source"],
            )
            db.add(new_metadata)


def create_photo_response(photo: Photo) -> PhotoRead:
    """Helper function to create PhotoRead from Photo model

    Args:
        photo: Photo database model instance

    Returns:
        PhotoRead response model with deserialized JSON fields
    """
    # Deserialize JSON fields and create response
    response_dict = {
        "uuid": photo.uuid,
        "masterFingerprint": photo.masterFingerprint,
        "original_filename": photo.original_filename,
        "date": photo.date,
        "description": photo.description,
        "title": photo.title,
        "keywords": deserialize_json_field(photo.keywords),
        "labels": deserialize_json_field(photo.labels),
        "albums": deserialize_json_field(photo.albums),
        "persons": deserialize_json_field(photo.persons),
        "faces": deserialize_json_field(photo.faces),
        "favorite": photo.favorite,
        "hidden": photo.hidden,
        "isphoto": photo.isphoto,
        "ismovie": photo.ismovie,
        "burst": photo.burst,
        "live_photo": photo.live_photo,
        "portrait": photo.portrait,
        "screenshot": photo.screenshot,
        "slow_mo": photo.slow_mo,
        "time_lapse": photo.time_lapse,
        "hdr": photo.hdr,
        "selfie": photo.selfie,
        "panorama": photo.panorama,
        "intrash": photo.intrash,
        "latitude": photo.latitude,
        "longitude": photo.longitude,
        "uti": photo.uti,
        "date_modified": photo.date_modified,
        "place": deserialize_json_field(photo.place),
        "exif": deserialize_json_field(photo.exif),
        "score": deserialize_json_field(photo.score),
        "search_info": deserialize_json_field(photo.search_info),
        "fields": deserialize_json_field(photo.fields),
        "height": photo.height,
        "width": photo.width,
        "size": photo.size,
        "orientation": photo.orientation,
        "s3_key_path": photo.s3_key_path,
        "s3_thumbnail_path": photo.s3_thumbnail_path,
        "s3_edited_path": photo.s3_edited_path,
        "s3_original_path": photo.s3_original_path,
        "s3_live_path": photo.s3_live_path,
        "library": photo.library,
        "uploaded_at": photo.uploaded_at,
        "filename": photo.filename,
        "file_path": photo.file_path,
        "content_type": photo.content_type,
        "file_size": photo.file_size,
        "url": photo.url,  # Use computed property
        "versions": (
            [
                VersionRead(
                    id=v.id,
                    photo_uuid=v.photo_uuid,
                    version=v.version,
                    s3_path=v.s3_path,
                    filename=v.filename,
                    width=v.width,
                    height=v.height,
                    size=v.size,
                    type=v.type,
                )
                for v in photo.versions
            ]
            if photo.versions
            else None
        ),
        "metadata": (
            [
                PhotoMetadataRead(
                    id=m.id,
                    photo_uuid=m.photo_uuid,
                    key=m.key,
                    value=m.value,
                    source=m.source,
                )
                for m in photo.photo_metadata
            ]
            if photo.photo_metadata
            else None
        ),
    }

    return PhotoRead(**response_dict)
