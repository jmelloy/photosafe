"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class VersionBase(BaseModel):
    """Version base schema"""

    version: str
    s3_path: str
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[int] = None
    type: Optional[str] = None


class VersionCreate(VersionBase):
    """Version create schema"""

    pass


class VersionResponse(VersionBase):
    """Version response schema"""

    id: int
    photo_uuid: Optional[str] = None

    class Config:
        from_attributes = True


class PhotoBase(BaseModel):
    """Photo base schema"""

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


class PhotoCreate(PhotoBase):
    """Photo create schema"""

    versions: Optional[List[VersionCreate]] = None


class PhotoUpdate(BaseModel):
    """Photo update schema - all fields optional"""

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


class PhotoResponse(PhotoBase):
    """Photo response schema"""

    uploaded_at: Optional[datetime] = None
    versions: Optional[List[VersionResponse]] = None

    # Backwards compatibility fields
    filename: Optional[str] = None
    file_path: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class AlbumBase(BaseModel):
    """Album base schema"""

    uuid: str
    title: str = ""
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AlbumCreate(AlbumBase):
    """Album create schema"""

    photos: Optional[List[str]] = None  # List of photo UUIDs


class AlbumUpdate(BaseModel):
    """Album update schema"""

    title: Optional[str] = None
    creation_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    photos: Optional[List[str]] = None  # List of photo UUIDs


class AlbumResponse(AlbumBase):
    """Album response schema"""

    class Config:
        from_attributes = True


# ============= USER SCHEMAS =============


class UserBase(BaseModel):
    """User base schema"""

    username: str
    email: str
    name: Optional[str] = None


class UserCreate(UserBase):
    """User create schema"""

    password: str


class UserResponse(UserBase):
    """User response schema"""

    id: int
    is_active: bool
    is_superuser: bool
    date_joined: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= LIBRARY SCHEMAS =============


class LibraryBase(BaseModel):
    """Library base schema"""

    name: str
    path: Optional[str] = None
    description: Optional[str] = None


class LibraryCreate(LibraryBase):
    """Library create schema"""

    pass


class LibraryUpdate(BaseModel):
    """Library update schema"""

    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None


class LibraryResponse(LibraryBase):
    """Library response schema"""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= TOKEN SCHEMAS =============


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema"""

    username: Optional[str] = None
