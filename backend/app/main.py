"""FastAPI Photo Gallery Backend"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import os
import shutil
from datetime import datetime
from pathlib import Path
from .database import engine, Base, get_db
from .models import Photo
from .schemas import PhotoResponse
from sqlalchemy.orm import Session
from fastapi import Depends

# Create database tables
Base.metadata.create_all(bind=engine)

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PhotoSafe Gallery API", "version": "1.0.0"}


@app.post("/api/photos/upload", response_model=PhotoResponse)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new photo"""
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
    
    # Create database record
    db_photo = Photo(
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        content_type=file.content_type,
        file_size=os.path.getsize(file_path)
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    return PhotoResponse(
        id=db_photo.id,
        filename=db_photo.filename,
        original_filename=db_photo.original_filename,
        url=f"/uploads/{db_photo.filename}",
        content_type=db_photo.content_type,
        file_size=db_photo.file_size,
        uploaded_at=db_photo.uploaded_at
    )


@app.get("/api/photos", response_model=List[PhotoResponse])
async def list_photos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all photos"""
    photos = db.query(Photo).order_by(Photo.uploaded_at.desc()).offset(skip).limit(limit).all()
    return [
        PhotoResponse(
            id=photo.id,
            filename=photo.filename,
            original_filename=photo.original_filename,
            url=f"/uploads/{photo.filename}",
            content_type=photo.content_type,
            file_size=photo.file_size,
            uploaded_at=photo.uploaded_at
        )
        for photo in photos
    ]


@app.get("/api/photos/{photo_id}", response_model=PhotoResponse)
async def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """Get a specific photo"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return PhotoResponse(
        id=photo.id,
        filename=photo.filename,
        original_filename=photo.original_filename,
        url=f"/uploads/{photo.filename}",
        content_type=photo.content_type,
        file_size=photo.file_size,
        uploaded_at=photo.uploaded_at
    )


@app.delete("/api/photos/{photo_id}")
async def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Delete file from disk
    file_path = Path(photo.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(photo)
    db.commit()
    
    return {"message": "Photo deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
