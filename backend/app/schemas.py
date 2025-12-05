"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel
from datetime import datetime


class PhotoResponse(BaseModel):
    """Photo response schema"""
    id: int
    filename: str
    original_filename: str
    url: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
