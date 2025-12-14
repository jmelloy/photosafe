"""Album API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    Album,
    Photo,
    AlbumRead,
    AlbumCreate,
    AlbumUpdate,
)

router = APIRouter(prefix="/api/albums", tags=["albums"])


@router.post("/", response_model=AlbumRead, status_code=201)
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


@router.put("/{uuid}/", response_model=AlbumRead)
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


@router.patch("/{uuid}/", response_model=AlbumRead)
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


@router.get("/", response_model=List[AlbumRead])
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


@router.get("/{uuid}/", response_model=AlbumRead)
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


@router.delete("/{uuid}/")
async def delete_album(uuid: str, db: Session = Depends(get_db)):
    """Delete an album by UUID"""
    album = db.query(Album).filter(Album.uuid == uuid).first()
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")

    # Delete from database
    db.delete(album)
    db.commit()

    return {"message": "Album deleted successfully"}
