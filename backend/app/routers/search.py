"""Search API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from sqlmodel import select

from ..database import get_db
from ..models import (
    Photo,
    User,
    SearchData,
    PaginatedPhotosResponse,
    SearchFiltersResponse,
)
from ..auth import get_current_active_user
from ..utils import create_photo_response

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/filters", response_model=SearchFiltersResponse)
async def get_search_filters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get available search filter values from search_data table"""
    
    # Get all search data entries for photos owned by current user
    # Join with photos to filter by owner
    query = (
        select(SearchData.key, SearchData.value)
        .join(Photo, SearchData.photo_uuid == Photo.uuid)
        .where(Photo.owner_id == current_user.id)
        .where(Photo.deleted_at.is_(None))
        .distinct()
    )
    
    results = db.exec(query).all()
    
    # Organize by key
    filters = {
        "places": set(),
        "labels": set(),
        "keywords": set(),
        "persons": set(),
        "albums": set(),
        "libraries": set(),
    }
    
    for key, value in results:
        if key == "place":
            filters["places"].add(value)
        elif key == "label":
            filters["labels"].add(value)
        elif key == "keyword":
            filters["keywords"].add(value)
        elif key == "person":
            filters["persons"].add(value)
        elif key == "album":
            filters["albums"].add(value)
        elif key == "library":
            filters["libraries"].add(value)
    
    return SearchFiltersResponse(
        places=sorted(list(filters["places"])),
        labels=sorted(list(filters["labels"])),
        keywords=sorted(list(filters["keywords"])),
        persons=sorted(list(filters["persons"])),
        albums=sorted(list(filters["albums"])),
        libraries=sorted(list(filters["libraries"])),
    )


@router.get("/", response_model=PaginatedPhotosResponse)
async def search_photos(
    page: int = 1,
    page_size: int = 50,
    search_text: Optional[str] = None,
    places: Optional[str] = None,
    labels: Optional[str] = None,
    keywords: Optional[str] = None,
    persons: Optional[str] = None,
    albums: Optional[str] = None,
    libraries: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search photos using the search_data table with multiple filter criteria.
    
    Multiple values for each filter can be provided as comma-separated strings.
    Photos matching ANY value in a filter category will be included (OR within category).
    Photos must match ALL specified filter categories (AND between categories).
    
    Example: places=Paris,London&labels=Sunset will find photos that are 
    (in Paris OR London) AND (have Sunset label)
    """
    # Validate pagination parameters
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50
    if page_size > 100:
        page_size = 100
    
    # Start with base query for user's photos
    query = (
        select(Photo)
        .where(Photo.owner_id == current_user.id)
        .where(Photo.deleted_at.is_(None))
        .options(joinedload(Photo.versions))
    )
    
    # Build search conditions from search_data table
    search_conditions = []
    
    # Helper function to parse comma-separated values
    def parse_filter_values(value_str: Optional[str]) -> List[str]:
        if not value_str:
            return []
        return [v.strip() for v in value_str.split(",") if v.strip()]
    
    # Parse filter values
    place_values = parse_filter_values(places)
    label_values = parse_filter_values(labels)
    keyword_values = parse_filter_values(keywords)
    person_values = parse_filter_values(persons)
    album_values = parse_filter_values(albums)
    library_values = parse_filter_values(libraries)
    
    # For each filter category with values, find matching photo UUIDs
    matching_photo_sets = []
    
    if place_values:
        place_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "place")
            .where(SearchData.value.in_(place_values))
        )
        matching_photos = db.exec(place_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    if label_values:
        label_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "label")
            .where(SearchData.value.in_(label_values))
        )
        matching_photos = db.exec(label_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    if keyword_values:
        keyword_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "keyword")
            .where(SearchData.value.in_(keyword_values))
        )
        matching_photos = db.exec(keyword_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    if person_values:
        person_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "person")
            .where(SearchData.value.in_(person_values))
        )
        matching_photos = db.exec(person_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    if album_values:
        album_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "album")
            .where(SearchData.value.in_(album_values))
        )
        matching_photos = db.exec(album_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    if library_values:
        library_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key == "library")
            .where(SearchData.value.in_(library_values))
        )
        matching_photos = db.exec(library_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    # Apply text search across title and description in search_data
    if search_text:
        text_query = (
            select(SearchData.photo_uuid)
            .where(SearchData.key.in_(["title", "description"]))
            .where(SearchData.value.ilike(f"%{search_text}%"))
        )
        matching_photos = db.exec(text_query).all()
        if matching_photos:
            matching_photo_sets.append(set(matching_photos))
    
    # Intersect all matching photo sets (AND logic between categories)
    if matching_photo_sets:
        final_photo_uuids = set.intersection(*matching_photo_sets)
        query = query.where(Photo.uuid.in_(final_photo_uuids))
    elif (
        place_values
        or label_values
        or keyword_values
        or person_values
        or album_values
        or library_values
        or search_text
    ):
        # If filters were specified but no matches found, return empty result
        return PaginatedPhotosResponse(
            items=[],
            page=page,
            page_size=page_size,
            has_more=False,
        )
    
    # Apply date range filters directly on Photo table
    if start_date:
        try:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(Photo.date >= start_dt)
        except ValueError:
            pass  # Skip invalid date format
    
    if end_date:
        try:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            # Include the entire end date
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.where(Photo.date <= end_dt)
        except ValueError:
            pass  # Skip invalid date format
    
    # Calculate offset
    skip = (page - 1) * page_size
    
    # Get photos with pagination (fetch one extra to check for more pages)
    photos = (
        db.exec(query.order_by(Photo.date.desc()).offset(skip).limit(page_size + 1))
        .unique()
        .all()
    )
    
    # Check if there are more pages
    has_more = len(photos) > page_size
    
    return PaginatedPhotosResponse(
        items=[create_photo_response(photo) for photo in photos[:page_size]],
        page=page,
        page_size=page_size,
        has_more=has_more,
    )
