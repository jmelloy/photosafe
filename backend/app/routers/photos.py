"""Photo API endpoints"""

import os
import shutil
import uuid as uuid_lib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from sqlmodel import select

from ..database import get_db
from ..models import (
    Photo,
    Version,
    User,
    PhotoRead,
    PhotoCreate,
    PhotoUpdate,
    PaginatedPhotosResponse,
    BatchPhotoRequest,
    BatchPhotoResult,
    BatchPhotoResponse,
)
from ..auth import get_current_active_user
from ..utils import (
    handle_library_upsert,
    create_photo_response,
    process_search_info_to_metadata,
    extend_photo_metadata,
)

router = APIRouter(prefix="/api/photos", tags=["photos"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/", response_model=PhotoRead, status_code=201)
async def create_photo(
    photo_data: PhotoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new photo (for sync_photos_linux compatibility)"""
    # Check if photo already exists
    existing = db.exec(select(Photo).where(Photo.uuid == photo_data.uuid)).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A photo with this uuid already exists: {photo_data.uuid}",
        )

    # Extract versions data and metadata
    versions_data = photo_data.versions or []
    metadata_entries = photo_data.metadata or []
    photo_dict = photo_data.model_dump(exclude={"versions", "metadata"})

    # Handle search_info for backward compatibility - convert to metadata
    if "search_info" in photo_dict and photo_dict["search_info"]:
        search_info = photo_dict.pop("search_info")
        metadata_from_search_info = process_search_info_to_metadata(
            search_info, source="legacy"
        )
        metadata_entries.extend(metadata_from_search_info)

    # Serialize JSON fields
    # photo_dict = serialize_photo_json_fields(photo_dict)

    # Create photo with owner
    db_photo = Photo(**photo_dict, owner_id=current_user.id)
    db.add(db_photo)
    db.flush()

    # Create versions
    for version_data in versions_data:
        db_version = Version(photo_uuid=db_photo.uuid, **version_data.model_dump())
        db.add(db_version)

    # Create metadata entries
    if metadata_entries:
        extend_photo_metadata(db_photo, metadata_entries, db)

    db.commit()
    db.refresh(db_photo)

    return create_photo_response(db_photo)


@router.patch("/{uuid}/", response_model=PhotoRead)
async def update_photo(
    uuid: str,
    photo_data: PhotoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a photo (for sync_photos_linux compatibility)"""
    db_photo = db.exec(select(Photo).where(Photo.uuid == uuid)).first()
    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Verify ownership
    if (
        db_photo.owner_id
        and db_photo.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this photo"
        )

    # Extract versions data and metadata
    versions_data = photo_data.versions or []
    metadata_entries = photo_data.metadata or []
    update_dict = photo_data.model_dump(exclude={"versions", "metadata"}, exclude_unset=True)

    # Handle search_info for backward compatibility - convert to metadata
    if "search_info" in update_dict and update_dict["search_info"]:
        search_info = update_dict.pop("search_info")
        # Determine source - default to "unknown", but could be "macos" if from macOS sync
        # The source will be set by the sync script in the metadata field
        metadata_from_search_info = process_search_info_to_metadata(
            search_info, source="legacy"
        )
        metadata_entries.extend(metadata_from_search_info)

    # Handle library name - upsert into libraries table
    if "library" in update_dict and update_dict["library"]:
        library_name = update_dict["library"]
        update_dict["library_id"] = handle_library_upsert(
            library_name, current_user, db
        )

    # Serialize JSON fields
    # update_dict = serialize_photo_json_fields(update_dict)

    # Update photo fields
    for key, value in update_dict.items():
        setattr(db_photo, key, value)

    # Update or create versions
    if versions_data:
        for version_data in versions_data:
            existing_version = db.exec(
                select(Version).where(
                    Version.photo_uuid == uuid, Version.version == version_data.version
                )
            ).first()

            if existing_version:
                for key, value in version_data.model_dump().items():
                    setattr(existing_version, key, value)
            else:
                db_version = Version(photo_uuid=uuid, **version_data.model_dump())
                db.add(db_version)

    # Extend metadata (upsert based on key+source)
    if metadata_entries:
        extend_photo_metadata(db_photo, metadata_entries, db)

    db.commit()
    db.refresh(db_photo)

    return create_photo_response(db_photo)


@router.post("/batch/", response_model=BatchPhotoResponse, status_code=200)
async def batch_create_or_update_photos(
    batch_data: BatchPhotoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create or update multiple photos in a single request"""
    results = []
    created_count = 0
    updated_count = 0
    error_count = 0

    for photo_data in batch_data.photos:
        try:
            # Check if photo already exists
            existing = db.exec(
                select(Photo).where(Photo.uuid == photo_data.uuid)
            ).first()

            if existing:
                # Update existing photo
                # Verify ownership
                if (
                    existing.owner_id
                    and existing.owner_id != current_user.id
                    and not current_user.is_superuser
                ):
                    results.append(
                        BatchPhotoResult(
                            uuid=photo_data.uuid,
                            success=False,
                            action="error",
                            error="Not authorized to update this photo",
                        )
                    )
                    error_count += 1
                    continue

                # Extract versions data and metadata
                versions_data = photo_data.versions or []
                metadata_entries = photo_data.metadata or []
                update_dict = photo_data.model_dump(
                    exclude={"versions", "metadata"}, exclude_unset=True
                )

                # Handle search_info for backward compatibility - convert to metadata
                if "search_info" in update_dict and update_dict["search_info"]:
                    search_info = update_dict.pop("search_info")
                    metadata_from_search_info = process_search_info_to_metadata(
                        search_info, source="legacy"
                    )
                    metadata_entries.extend(metadata_from_search_info)

                # Handle library name - upsert into libraries table
                if "library" in update_dict and update_dict["library"]:
                    library_name = update_dict["library"]
                    update_dict["library_id"] = handle_library_upsert(
                        library_name, current_user, db
                    )

                # Serialize JSON fields
                # update_dict = serialize_photo_json_fields(update_dict)

                # Update photo fields
                for key, value in update_dict.items():
                    setattr(existing, key, value)

                # Update or create versions
                if versions_data:
                    for version_data in versions_data:
                        existing_version = db.exec(
                            select(Version).where(
                                Version.photo_uuid == photo_data.uuid,
                                Version.version == version_data.version,
                            )
                        ).first()

                        if existing_version:
                            for key, value in version_data.model_dump().items():
                                setattr(existing_version, key, value)
                        else:
                            db_version = Version(
                                photo_uuid=photo_data.uuid, **version_data.model_dump()
                            )
                            db.add(db_version)

                # Extend metadata
                if metadata_entries:
                    extend_photo_metadata(existing, metadata_entries, db)

                db.flush()
                results.append(
                    BatchPhotoResult(
                        uuid=photo_data.uuid, success=True, action="updated"
                    )
                )
                updated_count += 1

            else:
                # Create new photo
                # Extract versions data and metadata
                versions_data = photo_data.versions or []
                metadata_entries = photo_data.metadata or []
                photo_dict = photo_data.model_dump(exclude={"versions", "metadata"})

                # Handle search_info for backward compatibility - convert to metadata
                if "search_info" in photo_dict and photo_dict["search_info"]:
                    search_info = photo_dict.pop("search_info")
                    metadata_from_search_info = process_search_info_to_metadata(
                        search_info, source="legacy"
                    )
                    metadata_entries.extend(metadata_from_search_info)

                # Serialize JSON fields
                # photo_dict = serialize_photo_json_fields(photo_dict)

                # Create photo with owner
                db_photo = Photo(**photo_dict, owner_id=current_user.id)
                db.add(db_photo)
                db.flush()

                # Create versions
                for version_data in versions_data:
                    db_version = Version(
                        photo_uuid=db_photo.uuid, **version_data.model_dump()
                    )
                    db.add(db_version)

                # Create metadata entries
                if metadata_entries:
                    extend_photo_metadata(db_photo, metadata_entries, db)

                db.flush()
                results.append(
                    BatchPhotoResult(
                        uuid=photo_data.uuid, success=True, action="created"
                    )
                )
                created_count += 1

        except Exception as e:
            results.append(
                BatchPhotoResult(
                    uuid=photo_data.uuid,
                    success=False,
                    action="error",
                    error=str(e),
                )
            )
            error_count += 1
            # Continue processing other photos instead of failing the entire batch

    # Commit all changes at once
    db.commit()

    return BatchPhotoResponse(
        results=results,
        total=len(batch_data.photos),
        created=created_count,
        updated=updated_count,
        errors=error_count,
    )


@router.get("/", response_model=PaginatedPhotosResponse)
async def list_photos(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    album: Optional[str] = None,
    keyword: Optional[str] = None,
    person: Optional[str] = None,
    library: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    favorite: Optional[bool] = None,
    isphoto: Optional[bool] = None,
    ismovie: Optional[bool] = None,
    screenshot: Optional[bool] = None,
    panorama: Optional[bool] = None,
    portrait: Optional[bool] = None,
    has_location: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all photos owned by the current user with pagination and optional filtering"""
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50
    if page_size > 100:
        page_size = 100

    # Superusers can see all photos, regular users only see their own
    if current_user.is_superuser:
        query = select(Photo)
    else:
        query = select(Photo).where(Photo.owner_id == current_user.id)

    # Eagerly load versions to avoid N+1 queries
    query = query.options(joinedload(Photo.versions))

    # Filter out soft-deleted photos by default
    query = query.where(Photo.deleted_at.is_(None))

    # Apply search filter - search in original_filename, title, and description
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Photo.original_filename.ilike(search_pattern),
                Photo.title.ilike(search_pattern),
                Photo.description.ilike(search_pattern),
            )
        )

    # Apply album filter
    if album:
        # Check if albums array contains the value (PostgreSQL)
        query = query.where(Photo.albums.contains([album]))

    # Apply keyword filter
    if keyword:
        query = query.where(Photo.keywords.contains([keyword]))

    # Apply person filter
    if person:
        query = query.where(Photo.persons.contains([person]))

    # Apply library filter
    if library:
        query = query.where(Photo.library == library)

    # Apply date range filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(Photo.date >= start_dt)
        except ValueError:
            pass  # Skip invalid date format

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.where(Photo.date <= end_dt)
        except ValueError:
            pass  # Skip invalid date format

    # Apply photo type filters
    if favorite is not None:
        query = query.where(Photo.favorite == favorite)

    if isphoto is not None:
        query = query.where(Photo.isphoto == isphoto)

    if ismovie is not None:
        query = query.where(Photo.ismovie == ismovie)

    if screenshot is not None:
        query = query.where(Photo.screenshot == screenshot)

    if panorama is not None:
        query = query.where(Photo.panorama == panorama)

    if portrait is not None:
        query = query.where(Photo.portrait == portrait)

    # Apply location filter
    if has_location is not None:
        if has_location:
            query = query.where(Photo.latitude.isnot(None), Photo.longitude.isnot(None))
        else:
            query = query.where(
                or_(Photo.latitude.is_(None), Photo.longitude.is_(None))
            )

    # Get total count before pagination
    # total = query.count()

    # Calculate offset
    skip = (page - 1) * page_size

    # Get photos with pagination
    photos = (
        db.exec(query.order_by(Photo.date.desc()).offset(skip).limit(page_size + 1))
        .unique()
        .all()
    )

    # Check if there are more pages
    has_more = len(photos) > page_size

    return PaginatedPhotosResponse(
        items=[create_photo_response(photo) for photo in photos[:page_size]],
        # total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/filters/")
async def get_photo_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, List[str]]:
    """Get available filter values for albums, keywords, persons, and libraries"""
    # Superusers can see all photos, regular users only see their own
    query = (
        select(Photo.albums, Photo.keywords, Photo.persons, Photo.library)
        .where(Photo.owner_id == current_user.id)
        .where(Photo.deleted_at.is_(None))
    ).distinct()

    # Get all photos for this user
    photos = db.exec(query).all()

    # Extract unique values from arrays and library field
    albums = set()
    keywords = set()
    persons = set()
    libraries = set()

    for photo in photos:
        if photo.albums:
            albums.update(photo.albums)
        if photo.keywords:
            keywords.update(photo.keywords)
        if photo.persons:
            persons.update(photo.persons)
        if photo.library:
            libraries.add(photo.library)

    return {
        "albums": sorted(list(albums)),
        "keywords": sorted(list(keywords)),
        "persons": sorted(list(persons)),
        "libraries": sorted(list(libraries)),
    }


@router.get("/blocks")
async def get_photo_blocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get photos grouped by year/month/day with counts and max dates.
    This endpoint groups photos without labels by date and returns a nested structure.
    """

    query = select(
        func.extract("year", Photo.date).label("year"),
        func.extract("month", Photo.date).label("month"),
        func.extract("day", Photo.date).label("day"),
        func.count().label("count"),
        func.max(func.coalesce(Photo.date_modified, Photo.date)).label("max_date"),
    )

    # Filter out soft-deleted photos
    query = query.where(Photo.owner_id == current_user.id)

    results = db.exec(
        query.group_by(
            func.extract("year", Photo.date),
            func.extract("month", Photo.date),
            func.extract("day", Photo.date),
        )
    ).all()

    # Build nested dictionary structure
    response = {}
    for row in results:
        year = int(row.year)
        month = int(row.month)
        day = int(row.day)

        if year not in response:
            response[year] = {}

        if month not in response[year]:
            response[year][month] = {}

        response[year][month][day] = {"count": int(row.count), "max_date": row.max_date}

    return response


@router.get("/{uuid}/", response_model=PhotoRead)
async def get_photo(
    uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific photo by UUID"""
    photo = db.exec(select(Photo).where(Photo.uuid == uuid)).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Verify ownership
    if (
        photo.owner_id
        and photo.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this photo")

    return create_photo_response(photo)


@router.delete("/{uuid}/")
async def delete_photo(
    uuid: str,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a photo by UUID (soft delete by default, use hard_delete=true for permanent deletion)"""
    photo = db.exec(select(Photo).where(Photo.uuid == uuid)).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Verify ownership
    if (
        photo.owner_id
        and photo.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this photo"
        )

    if hard_delete:
        # Delete file from disk if it exists
        if photo.file_path:
            file_path = Path(photo.file_path)
            if file_path.exists():
                file_path.unlink()

        # Delete from database (versions will be cascade deleted)
        db.delete(photo)
        db.commit()
        return {"message": "Photo permanently deleted"}
    else:
        # Soft delete - set deleted_at timestamp
        photo.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return {"message": "Photo deleted successfully"}


@router.post("/upload", response_model=PhotoRead)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Upload a new photo (legacy endpoint for backwards compatibility)"""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / filename

    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create database record with minimal fields
    db_photo = Photo(
        uuid=str(uuid_lib.uuid4()),
        original_filename=file.filename,
        date=datetime.now(timezone.utc),
        filename=filename,
        file_path=str(file_path),
        content_type=file.content_type,
        file_size=os.path.getsize(file_path),
        owner_id=current_user.id,
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)

    return create_photo_response(db_photo)
