"""FastAPI Photo Gallery Backend"""

import os
import traceback
from pathlib import Path

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .routers import auth, photos, albums, places, search
from .version import get_version, get_version_info
from .email import send_error_email

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


def _get_error_context(request: Request, exc: Exception) -> tuple[dict, str]:
    """Extract error context and traceback from request and exception."""
    context = {
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
    }
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return context, tb_str


# Exception handler for HTTPException with 500 status code
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException and send email for 500 errors."""
    # Only send email for 500 errors
    if exc.status_code >= 500:
        context, tb_str = _get_error_context(request, exc)
        send_error_email(exc, context=context, traceback_str=tb_str)
    
    # Return the original HTTPException response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Exception handler for all other unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and send email notification."""
    context, tb_str = _get_error_context(request, exc)
    send_error_email(exc, context=context, traceback_str=tb_str)
    
    # Return 500 response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


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
