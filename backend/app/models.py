"""Database models using SQLModel"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, DateTime, Integer, Boolean, Float, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid


# Association table for many-to-many relationship between albums and photos
album_photos = Table(
    "album_photos",
    SQLModel.metadata,
    Column("album_uuid", String, ForeignKey("albums.uuid")),
    Column("photo_uuid", String, ForeignKey("photos.uuid")),
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
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

    # Owner relationship
    owner_id: int = Field(foreign_key="users.id")

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
        sa_type=String,
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
    library_id: Optional[int] = Field(default=None, foreign_key="libraries.id")

    # For backwards compatibility with existing upload functionality
    filename: Optional[str] = Field(default=None, sa_type=String)
    file_path: Optional[str] = Field(default=None, sa_type=String)
    content_type: Optional[str] = Field(default=None, sa_type=String)
    file_size: Optional[int] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    # Owner relationship - matching Django Photo model
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Relationships
    owner: Optional["User"] = Relationship(back_populates="photos")
    library_ref: Optional["Library"] = Relationship(back_populates="photos")
    versions: List["Version"] = Relationship(
        back_populates="photo", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Version(SQLModel, table=True):
    """Photo version model"""

    __tablename__ = "versions"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    photo_uuid: Optional[str] = Field(default=None, foreign_key="photos.uuid")

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

    uuid: str = Field(primary_key=True, sa_type=String)
    title: str = Field(default="", sa_type=Text)
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Many-to-many relationship with photos
    # SQLModel doesn't have native many-to-many support, so we use sa_relationship_kwargs
    photos: List["Photo"] = Relationship(
        sa_relationship_kwargs={
            "secondary": album_photos,
            "backref": "photo_albums"
        }
    )

