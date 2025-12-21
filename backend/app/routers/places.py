"""API routes for place summaries and tasks"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional

from app.database import get_db
from app.models import PlaceSummary, PlaceSummaryRead, Task, TaskRead
from app.auth import get_current_user, User

router = APIRouter()


@router.get("/place-summaries", response_model=List[PlaceSummaryRead])
def get_place_summaries(
    country: Optional[str] = Query(None, description="Filter by country"),
    state_province: Optional[str] = Query(None, description="Filter by state/province"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get place summaries for map display.

    Returns aggregated place data with photo counts and date ranges.
    This is much faster than querying all photos for map display.
    """
    query = select(PlaceSummary).order_by(PlaceSummary.photo_count.desc())

    # Apply filters
    if country:
        query = query.where(PlaceSummary.country == country)
    if state_province:
        query = query.where(PlaceSummary.state_province == state_province)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    summaries = db.exec(query).all()
    return summaries


@router.get("/place-summaries/{summary_id}", response_model=PlaceSummaryRead)
def get_place_summary(
    summary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific place summary by ID"""
    summary = db.get(PlaceSummary, summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Place summary not found")
    return summary


@router.get("/tasks", response_model=List[TaskRead])
def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of tasks"""
    query = select(Task).order_by(Task.created_at.desc())

    if status:
        query = query.where(Task.status == status)
    if task_type:
        query = query.where(Task.task_type == task_type)

    query = query.limit(limit)

    tasks = db.exec(query).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific task by ID"""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
