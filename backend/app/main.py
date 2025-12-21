"""FastAPI Photo Gallery Backend"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import auth, photos, albums, places, search
from .version import get_version, get_version_info

# Database tables are now created via Alembic migrations
# To initialize the database, run: alembic upgrade head

app = FastAPI(title="PhotoSafe Gallery API", version=get_version())

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

# Include routers
app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(albums.router)
app.include_router(places.router, prefix="/api", tags=["places"])
app.include_router(search.router)


@app.get("/")
async def root():
    """Root endpoint"""
    version_info = get_version_info()
    return {"message": "PhotoSafe Gallery API", **version_info}


@app.get("/api/version")
async def version():
    """Get API version"""
    return get_version_info()


if __name__ == "__main__":
    import uvicorn

    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(app, host="0.0.0.0", port=8000, debug=debug)
