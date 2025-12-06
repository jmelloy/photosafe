"""Database models"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    Text,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base


# Association table for many-to-many relationship between albums and photos
album_photos = Table(
    "album_photos",
    Base.metadata,
    Column("album_uuid", String, ForeignKey("albums.uuid")),
    Column("photo_uuid", String, ForeignKey("photos.uuid")),
)


class User(Base):
    """User model matching Django User model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    date_joined = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    photos = relationship("Photo", back_populates="owner")


class Photo(Base):
    """Photo model matching Django Photo model"""

    __tablename__ = "photos"

    # Primary identifier
    uuid = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    masterFingerprint = Column(Text, nullable=True)

    # File information
    original_filename = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    title = Column(Text, nullable=True)

    # Arrays - using JSON for SQLite compatibility, can be ARRAY for PostgreSQL
    keywords = Column(Text, nullable=True)  # JSON string for array
    labels = Column(Text, nullable=True)  # JSON string for array
    albums = Column(Text, nullable=True)  # JSON string for array
    persons = Column(Text, nullable=True)  # JSON string for array

    # JSON fields
    faces = Column(Text, nullable=True)  # JSON string

    # Boolean flags
    favorite = Column(Boolean, nullable=True)
    hidden = Column(Boolean, nullable=True)
    isphoto = Column(Boolean, nullable=True)
    ismovie = Column(Boolean, nullable=True)
    burst = Column(Boolean, nullable=True)
    live_photo = Column(Boolean, nullable=True)
    portrait = Column(Boolean, nullable=True)
    screenshot = Column(Boolean, nullable=True)
    slow_mo = Column(Boolean, nullable=True)
    time_lapse = Column(Boolean, nullable=True)
    hdr = Column(Boolean, nullable=True)
    selfie = Column(Boolean, nullable=True)
    panorama = Column(Boolean, nullable=True)
    intrash = Column(Boolean, nullable=True)

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Media type
    uti = Column(Text, nullable=True)

    # Dates
    date_modified = Column(DateTime, nullable=True)

    # JSON fields
    place = Column(Text, nullable=True)  # JSON string
    exif = Column(Text, nullable=True)  # JSON string
    score = Column(Text, nullable=True)  # JSON string
    search_info = Column(Text, nullable=True)  # JSON string
    fields = Column(Text, nullable=True)  # JSON string

    # Dimensions and size
    height = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    size = Column(Integer, nullable=True)
    orientation = Column(Integer, nullable=True)

    # S3 paths
    s3_key_path = Column(Text, nullable=True)
    s3_thumbnail_path = Column(Text, nullable=True)
    s3_edited_path = Column(Text, nullable=True)
    s3_original_path = Column(Text, nullable=True)
    s3_live_path = Column(Text, nullable=True)

    # Library support
    library = Column(Text, nullable=True)

    # For backwards compatibility with existing upload functionality
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Owner relationship - matching Django Photo model
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="photos")
    versions = relationship(
        "Version", back_populates="photo", cascade="all, delete-orphan"
    )


class Version(Base):
    """Photo version model"""

    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    photo_uuid = Column(String, ForeignKey("photos.uuid"), nullable=True)

    version = Column(Text, nullable=False)
    s3_path = Column(Text, nullable=False)
    filename = Column(Text, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    size = Column(Integer, nullable=True)
    type = Column(Text, nullable=True)

    # Relationship
    photo = relationship("Photo", back_populates="versions")


class Album(Base):
    """Album model"""

    __tablename__ = "albums"

    uuid = Column(String, primary_key=True)
    title = Column(Text, nullable=False, default="")
    creation_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Many-to-many relationship with photos
    photos = relationship("Photo", secondary=album_photos, backref="photo_albums")
