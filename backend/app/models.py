"""Database models using SQLModel"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    Float,
    ForeignKey,
    Table,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import uuid
import os

# S3 base URL from environment or default
S3_BASE_URL = os.getenv("S3_BASE_URL", "https://photos.melloy.life")


# Association table for many-to-many relationship between albums and photos
album_photos = Table(
    "album_photos",
    SQLModel.metadata,
    Column("album_uuid", UUID(as_uuid=True), ForeignKey("albums.uuid"), index=True),
    Column("photo_uuid", UUID(as_uuid=True), ForeignKey("photos.uuid"), index=True),
)


class User(SQLModel, table=True):
    """User model matching Django User model"""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(unique=True, index=True, sa_type=String)
    email: str = Field(unique=True, index=True, sa_type=String)
    hashed_password: str = Field(sa_type=String)
    name: Optional[str] = Field(default=None, sa_type=String)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    date_joined: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # Relationships
    photos: List["Photo"] = Relationship(back_populates="owner")
    libraries: List["Library"] = Relationship(back_populates="owner")


class Library(SQLModel, table=True):
    """Library model for managing multiple photo libraries per user"""

    __tablename__ = "libraries"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(sa_type=String)
    path: Optional[str] = Field(default=None, sa_type=Text)
    description: Optional[str] = Field(default=None, sa_type=Text)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    )

    # Owner relationship
    owner_id: int = Field(foreign_key="users.id", index=True)

    # Relationships
    owner: Optional["User"] = Relationship(back_populates="libraries")
    photos: List["Photo"] = Relationship(back_populates="library_ref")


class Photo(SQLModel, table=True):
    """Photo model matching Django Photo model"""

    __tablename__ = "photos"

    # Primary identifier
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        sa_type=UUID(as_uuid=True),
    )
    masterFingerprint: Optional[str] = Field(default=None, sa_type=Text)

    # File information
    original_filename: str = Field(sa_type=Text)
    date: datetime
    description: Optional[str] = Field(default=None, sa_type=Text)
    title: Optional[str] = Field(default=None, sa_type=Text)

    # Arrays - PostgreSQL ARRAY type
    keywords: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String), nullable=True)
    )
    labels: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String), nullable=True)
    )
    albums: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String), nullable=True)
    )
    persons: Optional[List[str]] = Field(
        default=None, sa_column=Column(ARRAY(String), nullable=True)
    )

    # JSON fields - PostgreSQL JSONB type
    faces: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    # Boolean flags
    favorite: Optional[bool] = None
    hidden: Optional[bool] = None
    isphoto: Optional[bool] = None
    ismovie: Optional[bool] = None
    burst: Optional[bool] = None
    live_photo: Optional[bool] = None
    portrait: Optional[bool] = None
    screenshot: Optional[bool] = None
    slow_mo: Optional[bool] = None
    time_lapse: Optional[bool] = None
    hdr: Optional[bool] = None
    selfie: Optional[bool] = None
    panorama: Optional[bool] = None
    intrash: Optional[bool] = None

    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Media type
    uti: Optional[str] = Field(default=None, sa_type=Text)

    # Dates
    date_modified: Optional[datetime] = None

    # JSON fields - PostgreSQL JSONB type
    place: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    exif: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    score: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    search_info: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    fields: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    # Dimensions and size
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[int] = None
    orientation: Optional[int] = None

    # S3 paths
    s3_key_path: Optional[str] = Field(default=None, sa_type=Text)
    s3_thumbnail_path: Optional[str] = Field(default=None, sa_type=Text)
    s3_edited_path: Optional[str] = Field(default=None, sa_type=Text)
    s3_original_path: Optional[str] = Field(default=None, sa_type=Text)
    s3_live_path: Optional[str] = Field(default=None, sa_type=Text)

    # Library support - keep library string for backwards compatibility
    library: Optional[str] = Field(default=None, sa_type=Text)
    library_id: Optional[int] = Field(
        default=None, foreign_key="libraries.id", index=True
    )

    # For backwards compatibility with existing upload functionality
    filename: Optional[str] = Field(default=None, sa_type=String)
    file_path: Optional[str] = Field(default=None, sa_type=String)
    content_type: Optional[str] = Field(default=None, sa_type=String)
    file_size: Optional[int] = None
    uploaded_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Owner relationship - matching Django Photo model
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)

    # Relationships
    owner: Optional["User"] = Relationship(back_populates="photos")
    library_ref: Optional["Library"] = Relationship(back_populates="photos")
    versions: List["Version"] = Relationship(
        back_populates="photo", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def url(self) -> Optional[str]:
        """Compute URL for frontend display - prioritize S3 paths, then local file_path"""

        def build_s3_url(s3_path: str) -> Optional[str]:
            """Build full S3 URL from S3 path/key"""
            if not s3_path:
                return None
            # If already a full URL, return as-is
            if s3_path.startswith("http://") or s3_path.startswith("https://"):
                return s3_path
            # Otherwise, construct URL with base domain
            s3_path = s3_path.lstrip("/")
            return f"{S3_BASE_URL}/{s3_path}"

        # Check for S3 paths - prioritize thumbnail, then key path, then edited, then original
        if self.s3_thumbnail_path:
            return build_s3_url(self.s3_thumbnail_path)
        elif self.s3_key_path:
            return build_s3_url(self.s3_key_path)
        elif self.s3_edited_path:
            return build_s3_url(self.s3_edited_path)
        elif self.s3_original_path:
            return build_s3_url(self.s3_original_path)
        elif self.file_path:
            # Fallback to local file_path
            file_path_str = str(self.file_path).replace("\\", "/")

            # If file_path contains "uploads", extract the path from there
            if "uploads" in file_path_str:
                uploads_index = file_path_str.find("uploads")
                if uploads_index != -1:
                    return "/" + file_path_str[uploads_index:]
                else:
                    return f"/uploads/{Path(self.file_path).name}"
            else:
                # If no uploads in path, assume it's relative to uploads directory
                file_path = Path(self.file_path)
                if file_path.is_absolute():
                    return f"/uploads/{file_path.name}"
                else:
                    # Relative path - prepend /uploads if not already there
                    if not file_path_str.startswith("/"):
                        return f"/uploads/{file_path_str}"
                    else:
                        return file_path_str
        return None


class Version(SQLModel, table=True):
    """Photo version model"""

    __tablename__ = "versions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    photo_uuid: Optional[str] = Field(
        default=None, foreign_key="photos.uuid", index=True, sa_type=UUID(as_uuid=True)
    )

    version: str = Field(sa_type=Text)
    s3_path: str = Field(sa_type=Text)
    filename: Optional[str] = Field(default=None, sa_type=Text)
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    type: Optional[str] = Field(default=None, sa_type=Text)

    # Relationship
    photo: Optional["Photo"] = Relationship(back_populates="versions")


class Album(SQLModel, table=True):
    """Album model"""

    __tablename__ = "albums"

    uuid: str = Field(primary_key=True, sa_type=UUID(as_uuid=True))
    title: str = Field(default="", sa_type=Text)
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Many-to-many relationship with photos
    # SQLModel doesn't have native many-to-many support, so we use sa_relationship_kwargs
    photos: List["Photo"] = Relationship(
        sa_relationship_kwargs={"secondary": album_photos, "backref": "photo_albums"}
    )


# ============= READ/WRITE SCHEMA VARIANTS =============
# These classes are used for API request/response validation
# They exclude database-internal fields like relationships


class UserRead(SQLModel):
    """User read schema - for API responses"""

    id: int
    username: str
    email: str
    name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    date_joined: datetime
    last_login: Optional[datetime] = None


class UserCreate(SQLModel):
    """User create schema - for API requests"""

    username: str
    email: str
    password: str
    name: Optional[str] = None


class LibraryRead(SQLModel):
    """Library read schema - for API responses"""

    id: int
    name: str
    path: Optional[str] = None
    description: Optional[str] = None
    owner_id: int
    created_at: datetime
    updated_at: datetime


class LibraryCreate(SQLModel):
    """Library create schema - for API requests"""

    name: str
    path: Optional[str] = None
    description: Optional[str] = None


class LibraryUpdate(SQLModel):
    """Library update schema - for API requests"""

    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None


class VersionRead(SQLModel):
    """Version read schema - for API responses"""

    id: int
    photo_uuid: Optional[str] = None
    version: str
    s3_path: str
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    type: Optional[str] = None


class VersionCreate(SQLModel):
    """Version create schema - for API requests"""

    version: str
    s3_path: str
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    type: Optional[str] = None


class PhotoRead(SQLModel):
    """Photo read schema - for API responses"""

    uuid: str
    masterFingerprint: Optional[str] = None
    original_filename: str
    date: datetime
    description: Optional[str] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    albums: Optional[List[str]] = None
    persons: Optional[List[str]] = None
    faces: Optional[Dict[str, Any]] = None
    favorite: Optional[bool] = None
    hidden: Optional[bool] = None
    isphoto: Optional[bool] = None
    ismovie: Optional[bool] = None
    burst: Optional[bool] = None
    live_photo: Optional[bool] = None
    portrait: Optional[bool] = None
    screenshot: Optional[bool] = None
    slow_mo: Optional[bool] = None
    time_lapse: Optional[bool] = None
    hdr: Optional[bool] = None
    selfie: Optional[bool] = None
    panorama: Optional[bool] = None
    intrash: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    uti: Optional[str] = None
    date_modified: Optional[datetime] = None
    place: Optional[Dict[str, Any]] = None
    exif: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    search_info: Optional[Dict[str, Any]] = None
    fields: Optional[Dict[str, Any]] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[int] = None
    orientation: Optional[int] = None
    s3_key_path: Optional[str] = None
    s3_thumbnail_path: Optional[str] = None
    s3_edited_path: Optional[str] = None
    s3_original_path: Optional[str] = None
    s3_live_path: Optional[str] = None
    library: Optional[str] = None
    filename: Optional[str] = None
    file_path: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    url: Optional[str] = None  # Computed property
    versions: Optional[List[VersionRead]] = None

    class Config:
        from_attributes = True


class PhotoCreate(SQLModel):
    """Photo create schema - for API requests"""

    uuid: str
    masterFingerprint: Optional[str] = None
    original_filename: str
    date: datetime
    description: Optional[str] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    albums: Optional[List[str]] = None
    persons: Optional[List[str]] = None
    faces: Optional[Dict[str, Any]] = None
    favorite: Optional[bool] = None
    hidden: Optional[bool] = None
    isphoto: Optional[bool] = None
    ismovie: Optional[bool] = None
    burst: Optional[bool] = None
    live_photo: Optional[bool] = None
    portrait: Optional[bool] = None
    screenshot: Optional[bool] = None
    slow_mo: Optional[bool] = None
    time_lapse: Optional[bool] = None
    hdr: Optional[bool] = None
    selfie: Optional[bool] = None
    panorama: Optional[bool] = None
    intrash: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    uti: Optional[str] = None
    date_modified: Optional[datetime] = None
    place: Optional[Dict[str, Any]] = None
    exif: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    search_info: Optional[Dict[str, Any]] = None
    fields: Optional[Dict[str, Any]] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[int] = None
    orientation: Optional[int] = None
    s3_key_path: Optional[str] = None
    s3_thumbnail_path: Optional[str] = None
    s3_edited_path: Optional[str] = None
    s3_original_path: Optional[str] = None
    s3_live_path: Optional[str] = None
    library: Optional[str] = None
    versions: Optional[List[VersionCreate]] = None


class PhotoUpdate(SQLModel):
    """Photo update schema - for API requests (all fields optional)"""

    masterFingerprint: Optional[str] = None
    original_filename: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    albums: Optional[List[str]] = None
    persons: Optional[List[str]] = None
    faces: Optional[Dict[str, Any]] = None
    favorite: Optional[bool] = None
    hidden: Optional[bool] = None
    isphoto: Optional[bool] = None
    ismovie: Optional[bool] = None
    burst: Optional[bool] = None
    live_photo: Optional[bool] = None
    portrait: Optional[bool] = None
    screenshot: Optional[bool] = None
    slow_mo: Optional[bool] = None
    time_lapse: Optional[bool] = None
    hdr: Optional[bool] = None
    selfie: Optional[bool] = None
    panorama: Optional[bool] = None
    intrash: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    uti: Optional[str] = None
    date_modified: Optional[datetime] = None
    place: Optional[Dict[str, Any]] = None
    exif: Optional[Dict[str, Any]] = None
    score: Optional[Dict[str, Any]] = None
    search_info: Optional[Dict[str, Any]] = None
    fields: Optional[Dict[str, Any]] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[int] = None
    orientation: Optional[int] = None
    s3_key_path: Optional[str] = None
    s3_thumbnail_path: Optional[str] = None
    s3_edited_path: Optional[str] = None
    s3_original_path: Optional[str] = None
    s3_live_path: Optional[str] = None
    library: Optional[str] = None
    versions: Optional[List[VersionCreate]] = None


class AlbumRead(SQLModel):
    """Album read schema - for API responses"""

    uuid: str
    title: str
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlbumCreate(SQLModel):
    """Album create schema - for API requests"""

    uuid: str
    title: str = ""
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    photos: Optional[List[str]] = None  # List of photo UUIDs


class AlbumUpdate(SQLModel):
    """Album update schema - for API requests"""

    title: Optional[str] = None
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    photos: Optional[List[str]] = None  # List of photo UUIDs


# ============= ADDITIONAL SCHEMAS =============


class Token(SQLModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(SQLModel):
    """Token data schema"""

    username: Optional[str] = None


class RefreshTokenRequest(SQLModel):
    """Refresh token request schema"""

    refresh_token: str


class PaginatedPhotosResponse(SQLModel):
    """Paginated photos response schema"""

    items: List[PhotoRead]
    total: Optional[int] = None
    page: int
    page_size: int
    has_more: bool


class BatchPhotoRequest(SQLModel):
    """Batch photo create/update request schema"""

    photos: List[PhotoCreate]


class BatchPhotoResult(SQLModel):
    """Result for a single photo in batch operation"""

    uuid: str
    success: bool
    action: str  # 'created', 'updated', or 'error'
    error: Optional[str] = None


class BatchPhotoResponse(SQLModel):
    """Batch photo operation response schema"""

    results: List[BatchPhotoResult]
    total: int
    created: int
    updated: int
    errors: int
