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


def bulk_update_place_summaries(db: Session) -> int:
    """Bulk update place summaries for all photos with place data

    Replaces all existing place summaries with fresh aggregations from photos.
    Uses a single SQL query to group photos by location and place data,
    calculating statistics like photo counts, date ranges, and selecting the
    most detailed place data for each unique location.

    The unique constraint on (latitude, longitude) ensures one summary per location.

    Args:
        db: Database session

    Returns:
        Number of place summaries created/updated
    """
    from sqlalchemy import text

    # First, clear existing summaries to avoid conflicts
    db.execute(text("DELETE FROM place_summaries"))

    # Bulk insert with aggregated data from photos
    # Group by latitude and longitude, selecting the most detailed place data
    sql = text("""
        WITH aggregated_places AS (
            SELECT 
                latitude, 
                longitude,
                count(*) as photo_count,
                min(date) as first_photo_date,
                max(date) as last_photo_date,
                -- Select place with longest JSON representation (most detailed)
                (array_agg(place ORDER BY length(place::text) DESC))[1] as place_data
            FROM photos
            WHERE place IS NOT NULL 
                AND place <> '{}'::jsonb 
                AND latitude IS NOT NULL 
                AND longitude IS NOT NULL
            GROUP BY latitude, longitude
        )
        INSERT INTO place_summaries 
            (latitude, longitude, place_name, country, state_province, city, 
             photo_count, first_photo_date, last_photo_date, place_data, updated_at)
        SELECT 
            latitude, 
            longitude,
            COALESCE(
                place_data->>'name',
                place_data->>'name_user_defined',
                place_data->>'name_locality',
                place_data->>'country',
                place_data->>'name_country',
                'Unknown'
            ) AS place_name,
            COALESCE(
                place_data->>'country',
                place_data->'names'->'country'->>0,
                place_data->>'name_country'
            ) AS country,
            COALESCE(
                place_data->'names'->'state_province'->>0,
                place_data->>'admin1',
                place_data->>'name_administrative_area',
                place_data->>'name_sub_administrative_area'
            ) AS state_province,
            COALESCE(
                place_data->'names'->'city'->>0,
                place_data->>'admin2',
                place_data->>'name_locality',
                place_data->>'name_sub_locality'
            ) AS city,
            photo_count,
            first_photo_date,
            last_photo_date,
            place_data,
            NOW() as updated_at
        FROM aggregated_places
    """)

    result = db.execute(sql)
    db.commit()

    # Count the number of summaries created
    count_result = db.execute(text("SELECT COUNT(*) FROM place_summaries"))
    row_count = count_result.scalar() or 0

    return row_count
