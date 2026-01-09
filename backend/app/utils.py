"""Utility functions for photo processing"""

import json
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import select, Session
from .models import (
    Photo,
    User,
    Library,
    VersionRead,
    PhotoRead,
    SearchData,
    PlaceSummary,
)

# Batch size for committing search_data population
SEARCH_DATA_BATCH_SIZE = 100


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
    library = db.exec(
        select(Library).where(
            Library.owner_id == current_user.id,
            Library.name == library_name,
        )
    ).first()
    if not library:
        library = Library(
            name=library_name,
            owner_id=current_user.id,
        )
        db.add(library)
        db.flush()
    return library.id


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
    }

    return PhotoRead(**response_dict)


def populate_search_data_for_photo(photo: Photo, db: Session) -> None:
    """Populate search_data table entries for a single photo

    Extracts searchable metadata from photo and creates search_data entries.
    This function handles:
    - labels (from labels array)
    - keywords (from keywords array)
    - persons (from persons array)
    - albums (from albums array)
    - place (from place.name_* hierarchy)
    - description (from description field)
    - title (from title field)

    Uses PostgreSQL's ON CONFLICT DO NOTHING to handle duplicates at the database level.

    Args:
        photo: Photo model instance to process
        db: Database session
    """
    # Delete existing search data for this photo
    db.exec(delete(SearchData).where(SearchData.photo_uuid == photo.uuid))

    search_entries = []

    # Add labels
    if photo.labels:
        for label in photo.labels:
            if label:
                search_entries.append(
                    {"photo_uuid": photo.uuid, "key": "label", "value": label}
                )

    # Add keywords
    if photo.keywords:
        for keyword in photo.keywords:
            if keyword:
                search_entries.append(
                    {"photo_uuid": photo.uuid, "key": "keyword", "value": keyword}
                )

    # Add persons
    if photo.persons:
        for person in photo.persons:
            if person:
                search_entries.append(
                    {"photo_uuid": photo.uuid, "key": "person", "value": person}
                )

    # Add albums
    if photo.albums:
        for album in photo.albums:
            if album:
                search_entries.append(
                    {"photo_uuid": photo.uuid, "key": "album", "value": album}
                )

    # Add place data
    if photo.place:
        place_data = (
            deserialize_json_field(photo.place)
            if isinstance(photo.place, str)
            else photo.place
        )
        if place_data and isinstance(place_data, dict):
            # Extract place hierarchy
            place_fields = [
                "name",
                "name_user_defined",
                "name_area_of_interest",
                "name_sub_locality",
                "name_locality",
                "name_sub_administrative_area",
                "name_administrative_area",
                "name_country",
            ]
            for field in place_fields:
                if field in place_data and place_data[field]:
                    search_entries.append(
                        {
                            "photo_uuid": photo.uuid,
                            "key": "place",
                            "value": str(place_data[field]),
                        }
                    )

    # Add description
    if photo.description and photo.description.strip():
        search_entries.append(
            {
                "photo_uuid": photo.uuid,
                "key": "description",
                "value": photo.description.strip(),
            }
        )

    # Add title
    if photo.title and photo.title.strip():
        search_entries.append(
            {"photo_uuid": photo.uuid, "key": "title", "value": photo.title.strip()}
        )

    # Add library
    if photo.library:
        search_entries.append(
            {"photo_uuid": photo.uuid, "key": "library", "value": photo.library}
        )

    # Bulk insert all entries using ON CONFLICT DO NOTHING to handle duplicates
    if search_entries:
        stmt = insert(SearchData.__table__).values(search_entries)
        stmt = stmt.on_conflict_do_nothing(constraint="uq_search_data_photo_key_value")
        db.execute(stmt)


def populate_search_data_for_all_photos(db: Session) -> int:
    """Populate search_data table for all photos in the database

    This is a maintenance function that can be run to rebuild the search_data
    table from scratch.

    Args:
        db: Database session

    Returns:
        Number of photos processed
    """
    # Get all photos
    photos = db.exec(select(Photo)).all()

    count = 0
    for photo in photos:
        populate_search_data_for_photo(photo, db)
        count += 1

        # Commit in batches
        if count % SEARCH_DATA_BATCH_SIZE == 0:
            db.commit()

    # Final commit
    db.commit()

    return count


def update_place_summary_for_photo(photo: Photo, db: Session) -> None:
    """Update place summary for a single photo with place data using PostgreSQL upsert

    Creates or updates a PlaceSummary record based on the photo's place information.
    Uses PostgreSQL's INSERT ... ON CONFLICT DO UPDATE for atomic upserts.
    If the photo has no place data, this function does nothing.

    Args:
        photo: Photo model instance to process
        db: Database session
    """
    if not photo.place:
        return

    # Deserialize place data if needed
    place_data = (
        deserialize_json_field(photo.place)
        if isinstance(photo.place, str)
        else photo.place
    )
    if not place_data or not isinstance(place_data, dict):
        return

    # Extract place name (use country if no specific name)
    place_name = (
        place_data.get("name")
        or place_data.get("name_user_defined")
        or place_data.get("name_locality")
        or place_data.get("country")
        or place_data.get("name_country")
        or "Unknown"
    )

    # Extract place hierarchy fields
    country = place_data.get("country") or place_data.get("name_country")
    state_province = (
        place_data.get("admin1")
        or place_data.get("name_administrative_area")
        or place_data.get("name_sub_administrative_area")
    )
    city = (
        place_data.get("admin2")
        or place_data.get("name_locality")
        or place_data.get("name_sub_locality")
    )

    # Use PostgreSQL upsert with raw SQL for atomic operation
    from sqlalchemy import text

    sql = text(
        """
        INSERT INTO place_summaries 
            (place_name, latitude, longitude, photo_count, first_photo_date, last_photo_date, 
             country, state_province, city, place_data, updated_at)
        VALUES 
            (:place_name, :latitude, :longitude, 1, :photo_date, :photo_date,
             :country, :state_province, :city, :place_data, :updated_at)
        ON CONFLICT (place_name) 
        DO UPDATE SET
            photo_count = place_summaries.photo_count + 1,
            first_photo_date = LEAST(place_summaries.first_photo_date, EXCLUDED.first_photo_date),
            last_photo_date = GREATEST(place_summaries.last_photo_date, EXCLUDED.last_photo_date),
            latitude = COALESCE(place_summaries.latitude, EXCLUDED.latitude),
            longitude = COALESCE(place_summaries.longitude, EXCLUDED.longitude),
            country = COALESCE(place_summaries.country, EXCLUDED.country),
            state_province = COALESCE(place_summaries.state_province, EXCLUDED.state_province),
            city = COALESCE(place_summaries.city, EXCLUDED.city),
            place_data = COALESCE(place_summaries.place_data, EXCLUDED.place_data),
            updated_at = EXCLUDED.updated_at
    """
    )

    db.execute(
        sql,
        {
            "place_name": place_name,
            "latitude": photo.latitude,
            "longitude": photo.longitude,
            "photo_date": photo.date,
            "country": country,
            "state_province": state_province,
            "city": city,
            "place_data": json.dumps(place_data) if place_data else None,
            "updated_at": datetime.now(timezone.utc),
        },
    )
