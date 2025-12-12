"""FastAPI Photo Gallery Backend"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Dict
import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from .database import engine, get_db
from .models import (
    Photo,
    Album,
    Version,
    User,
    Library,
    PhotoRead,
    PhotoCreate,
    PhotoUpdate,
    AlbumRead,
    AlbumCreate,
    AlbumUpdate,
    VersionRead,
    UserCreate,
    UserRead,
    Token,
    PaginatedPhotosResponse,
    BatchPhotoRequest,
    BatchPhotoResult,
    BatchPhotoResponse,
)
from .auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import Depends

# Database tables are now created via Alembic migrations
# To initialize the database, run: alembic upgrade head

app = FastAPI(title="PhotoSafe Gallery API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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


def serialize_photo_json_fields(photo_dict):
    """Serialize JSON fields in a photo dictionary for database storage
    
    Note: Only serializes JSONB fields (faces, place, exif, score, search_info, fields).
    Array fields (keywords, labels, albums, persons) are stored as PostgreSQL arrays 
    and should NOT be JSON-serialized.
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PhotoSafe Gallery API", "version": "1.0.0"}


# ============= AUTHENTICATION ENDPOINTS =============


@app.post("/api/auth/register", response_model=UserRead, status_code=201)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


# ============= PHOTO ENDPOINTS =============


@app.post("/api/photos/", response_model=PhotoRead, status_code=201)
async def create_photo(
    photo_data: PhotoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new photo (for sync_photos_linux compatibility)"""
    # Check if photo already exists
    existing = db.query(Photo).filter(Photo.uuid == photo_data.uuid).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"A photo with this uuid already exists: {photo_data.uuid}",
        )

    # Extract versions data
    versions_data = photo_data.versions or []
    photo_dict = photo_data.model_dump(exclude={"versions"})

    # Serialize JSON fields
    photo_dict = serialize_photo_json_fields(photo_dict)

    # Create photo with owner
    db_photo = Photo(**photo_dict, owner_id=current_user.id)
    db.add(db_photo)
    db.flush()

    # Create versions
    for version_data in versions_data:
        db_version = Version(photo_uuid=db_photo.uuid, **version_data.model_dump())
        db.add(db_version)

    db.commit()
    db.refresh(db_photo)

    return create_photo_response(db_photo)


@app.patch("/api/photos/{uuid}/", response_model=PhotoRead)
async def update_photo(
    uuid: str,
    photo_data: PhotoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a photo (for sync_photos_linux compatibility)"""
    db_photo = db.query(Photo).filter(Photo.uuid == uuid).first()
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

    # Extract versions data
    versions_data = photo_data.versions or []
    update_dict = photo_data.model_dump(exclude={"versions"}, exclude_unset=True)

    # Handle library name - upsert into libraries table
    if "library" in update_dict and update_dict["library"]:
        library_name = update_dict["library"]
        update_dict["library_id"] = handle_library_upsert(
            library_name, current_user, db
        )

    # Serialize JSON fields
    update_dict = serialize_photo_json_fields(update_dict)

    # Update photo fields
    for key, value in update_dict.items():
        setattr(db_photo, key, value)

    # Update or create versions
    if versions_data:
        for version_data in versions_data:
            existing_version = (
                db.query(Version)
                .filter(
                    Version.photo_uuid == uuid, Version.version == version_data.version
                )
                .first()
            )

            if existing_version:
                for key, value in version_data.model_dump().items():
                    setattr(existing_version, key, value)
            else:
                db_version = Version(photo_uuid=uuid, **version_data.model_dump())
                db.add(db_version)

    db.commit()
    db.refresh(db_photo)

    return create_photo_response(db_photo)


@app.post("/api/photos/batch/", response_model=BatchPhotoResponse, status_code=200)
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
            existing = db.query(Photo).filter(Photo.uuid == photo_data.uuid).first()

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

                # Extract versions data
                versions_data = photo_data.versions or []
                update_dict = photo_data.model_dump(
                    exclude={"versions"}, exclude_unset=True
                )

                # Handle library name - upsert into libraries table
                if "library" in update_dict and update_dict["library"]:
                    library_name = update_dict["library"]
                    update_dict["library_id"] = handle_library_upsert(
                        library_name, current_user, db
                    )

                # Serialize JSON fields
                update_dict = serialize_photo_json_fields(update_dict)

                # Update photo fields
                for key, value in update_dict.items():
                    setattr(existing, key, value)

                # Update or create versions
                if versions_data:
                    for version_data in versions_data:
                        existing_version = (
                            db.query(Version)
                            .filter(
                                Version.photo_uuid == photo_data.uuid,
                                Version.version == version_data.version,
                            )
                            .first()
                        )

                        if existing_version:
                            for key, value in version_data.model_dump().items():
                                setattr(existing_version, key, value)
                        else:
                            db_version = Version(
                                photo_uuid=photo_data.uuid, **version_data.model_dump()
                            )
                            db.add(db_version)

                db.flush()
                results.append(
                    BatchPhotoResult(
                        uuid=photo_data.uuid, success=True, action="updated"
                    )
                )
                updated_count += 1

            else:
                # Create new photo
                # Extract versions data
                versions_data = photo_data.versions or []
                photo_dict = photo_data.model_dump(exclude={"versions"})

                # Serialize JSON fields
                photo_dict = serialize_photo_json_fields(photo_dict)

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


@app.get("/api/photos/", response_model=PaginatedPhotosResponse)
async def list_photos(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    album: Optional[str] = None,
    keyword: Optional[str] = None,
    person: Optional[str] = None,
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
        query = db.query(Photo)
    else:
        query = db.query(Photo).filter(Photo.owner_id == current_user.id)

    # Apply search filter - search in original_filename, title, and description
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Photo.original_filename.ilike(search_pattern),
                Photo.title.ilike(search_pattern),
                Photo.description.ilike(search_pattern),
            )
        )

    # Apply album filter
    if album:
        # Check if albums array contains the value (PostgreSQL)
        query = query.filter(Photo.albums.contains([album]))

    # Apply keyword filter
    if keyword:
        query = query.filter(Photo.keywords.contains([keyword]))

    # Apply person filter
    if person:
        query = query.filter(Photo.persons.contains([person]))

    # Apply date range filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Photo.date >= start_dt)
        except ValueError:
            pass  # Skip invalid date format

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(Photo.date <= end_dt)
        except ValueError:
            pass  # Skip invalid date format

    # Apply photo type filters
    if favorite is not None:
        query = query.filter(Photo.favorite == favorite)

    if isphoto is not None:
        query = query.filter(Photo.isphoto == isphoto)

    if ismovie is not None:
        query = query.filter(Photo.ismovie == ismovie)

    if screenshot is not None:
        query = query.filter(Photo.screenshot == screenshot)

    if panorama is not None:
        query = query.filter(Photo.panorama == panorama)

    if portrait is not None:
        query = query.filter(Photo.portrait == portrait)

    # Apply location filter
    if has_location is not None:
        if has_location:
            query = query.filter(Photo.latitude.isnot(None), Photo.longitude.isnot(None))
        else:
            query = query.filter(or_(Photo.latitude.is_(None), Photo.longitude.is_(None)))

    # Get total count before pagination
    total = query.count()

    # Calculate offset
    skip = (page - 1) * page_size

    # Get photos with pagination
    photos = query.order_by(Photo.date.desc()).offset(skip).limit(page_size).all()

    # Check if there are more pages
    has_more = (skip + page_size) < total

    return PaginatedPhotosResponse(
        items=[create_photo_response(photo) for photo in photos],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@app.get("/api/photos/filters/")
async def get_photo_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, List[str]]:
    """Get available filter values for albums, keywords, and persons"""
    # Superusers can see all photos, regular users only see their own
    if current_user.is_superuser:
        query = db.query(Photo)
    else:
        query = db.query(Photo).filter(Photo.owner_id == current_user.id)
    
    # Get all photos for this user
    photos = query.all()
    
    # Extract unique values from arrays
    albums = set()
    keywords = set()
    persons = set()
    
    for photo in photos:
        if photo.albums:
            albums.update(photo.albums)
        if photo.keywords:
            keywords.update(photo.keywords)
        if photo.persons:
            persons.update(photo.persons)
    
    return {
        "albums": sorted(list(albums)),
        "keywords": sorted(list(keywords)),
        "persons": sorted(list(persons)),
    }


@app.get("/api/photos/{uuid}/", response_model=PhotoRead)
async def get_photo(
    uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific photo by UUID"""
    photo = db.query(Photo).filter(Photo.uuid == uuid).first()
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


@app.delete("/api/photos/{uuid}/")
async def delete_photo(
    uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a photo by UUID"""
    photo = db.query(Photo).filter(Photo.uuid == uuid).first()
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

    # Delete file from disk if it exists
    if photo.file_path:
        file_path = Path(photo.file_path)
        if file_path.exists():
            file_path.unlink()

    # Delete from database (versions will be cascade deleted)
    db.delete(photo)
    db.commit()

    return {"message": "Photo deleted successfully"}


@app.get("/api/photos/blocks")
async def get_photo_blocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get photos grouped by year/month/day with counts and max dates.
    This endpoint groups photos without labels by date and returns a nested structure.
    """

    query = db.query(
        func.extract("year", Photo.date).label("year"),
        func.extract("month", Photo.date).label("month"),
        func.extract("day", Photo.date).label("day"),
        func.count().label("count"),
        func.max(func.coalesce(Photo.date_modified, Photo.date)).label("max_date"),
    ).filter(or_(Photo.labels == None, func.array_length(Photo.labels, 1) == None))

    # Filter by owner if not superuser
    if not current_user.is_superuser:
        query = query.filter(Photo.owner_id == current_user.id)

    results = query.group_by(
        func.extract("year", Photo.date),
        func.extract("month", Photo.date),
        func.extract("day", Photo.date),
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


def create_photo_response(photo: Photo) -> PhotoRead:
    """Helper function to create PhotoRead from Photo model"""
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


# ============= ALBUM ENDPOINTS =============


@app.post("/api/albums/", response_model=AlbumRead, status_code=201)
async def create_album(album_data: AlbumCreate, db: Session = Depends(get_db)):
    """Create a new album (for sync_photos_linux compatibility)"""
    # Check if album already exists
    existing = db.query(Album).filter(Album.uuid == album_data.uuid).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"An album with this uuid already exists: {album_data.uuid}",
        )

    # Extract photos list
    photo_uuids = album_data.photos or []
    album_dict = album_data.model_dump(exclude={"photos"})

    # Create album
    db_album = Album(**album_dict)
    db.add(db_album)
    db.flush()

    # Add photos to album
    for photo_uuid in photo_uuids:
        photo = db.query(Photo).filter(Photo.uuid == photo_uuid).first()
        if photo:
            db_album.photos.append(photo)

    db.commit()
    db.refresh(db_album)

    return AlbumRead(
        uuid=db_album.uuid,
        title=db_album.title,
        creation_date=db_album.creation_date,
        start_date=db_album.start_date,
        end_date=db_album.end_date,
    )


@app.put("/api/albums/{uuid}/", response_model=AlbumRead)
async def update_or_create_album(
    uuid: str, album_data: AlbumCreate, db: Session = Depends(get_db)
):
    """Update or create an album (for sync_photos_linux compatibility)"""
    db_album = db.query(Album).filter(Album.uuid == uuid).first()

    # Extract photos list
    photo_uuids = album_data.photos or []

    if db_album:
        # Update existing album
        db_album.title = album_data.title
        db_album.creation_date = album_data.creation_date
        db_album.start_date = album_data.start_date
        db_album.end_date = album_data.end_date

        # Clear and re-add photos
        db_album.photos.clear()
        for photo_uuid in photo_uuids:
            photo = db.query(Photo).filter(Photo.uuid == photo_uuid).first()
            if photo:
                db_album.photos.append(photo)
    else:
        # Create new album
        album_dict = album_data.model_dump(exclude={"photos"})
        album_dict["uuid"] = uuid  # Use UUID from path
        db_album = Album(**album_dict)
        db.add(db_album)
        db.flush()

        # Add photos to album
        for photo_uuid in photo_uuids:
            photo = db.query(Photo).filter(Photo.uuid == photo_uuid).first()
            if photo:
                db_album.photos.append(photo)

    db.commit()
    db.refresh(db_album)

    return AlbumRead(
        uuid=db_album.uuid,
        title=db_album.title,
        creation_date=db_album.creation_date,
        start_date=db_album.start_date,
        end_date=db_album.end_date,
    )


@app.patch("/api/albums/{uuid}/", response_model=AlbumRead)
async def patch_album(
    uuid: str, album_data: AlbumUpdate, db: Session = Depends(get_db)
):
    """Partially update an album (Django DRF compatibility)"""
    db_album = db.query(Album).filter(Album.uuid == uuid).first()
    if not db_album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Extract photos list if provided
    photo_uuids = album_data.photos

    # Update only provided fields
    update_dict = album_data.model_dump(exclude={"photos"}, exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_album, key, value)

    # Update photos if provided
    if photo_uuids is not None:
        db_album.photos.clear()
        for photo_uuid in photo_uuids:
            photo = db.query(Photo).filter(Photo.uuid == photo_uuid).first()
            if photo:
                db_album.photos.append(photo)

    db.commit()
    db.refresh(db_album)

    return AlbumRead(
        uuid=db_album.uuid,
        title=db_album.title,
        creation_date=db_album.creation_date,
        start_date=db_album.start_date,
        end_date=db_album.end_date,
    )


@app.get("/api/albums/", response_model=List[AlbumRead])
async def list_albums(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all albums"""
    albums = db.query(Album).offset(skip).limit(limit).all()
    return [
        AlbumRead(
            uuid=album.uuid,
            title=album.title,
            creation_date=album.creation_date,
            start_date=album.start_date,
            end_date=album.end_date,
        )
        for album in albums
    ]


@app.get("/api/albums/{uuid}/", response_model=AlbumRead)
async def get_album(uuid: str, db: Session = Depends(get_db)):
    """Get a specific album by UUID"""
    album = db.query(Album).filter(Album.uuid == uuid).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    return AlbumRead(
        uuid=album.uuid,
        title=album.title,
        creation_date=album.creation_date,
        start_date=album.start_date,
        end_date=album.end_date,
    )


@app.delete("/api/albums/{uuid}/")
async def delete_album(uuid: str, db: Session = Depends(get_db)):
    """Delete an album by UUID"""
    album = db.query(Album).filter(Album.uuid == uuid).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Delete from database
    db.delete(album)
    db.commit()

    return {"message": "Album deleted successfully"}


# ============= LEGACY UPLOAD ENDPOINT =============


@app.post("/api/photos/upload", response_model=PhotoRead)
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
    import uuid

    db_photo = Photo(
        uuid=str(uuid.uuid4()),
        original_filename=file.filename,
        date=datetime.utcnow(),
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


if __name__ == "__main__":
    import uvicorn

    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(app, host="0.0.0.0", port=8000, debug=debug)
