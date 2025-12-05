"""Database models"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base


class Photo(Base):
    """Photo model"""
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    original_filename = Column(String)
    file_path = Column(String)
    content_type = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
