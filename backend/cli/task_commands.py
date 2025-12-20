#!/usr/bin/env python
"""PhotoSafe CLI - Task processing commands"""

import click
from sqlalchemy import select, and_, or_
from sqlmodel import Session
from datetime import datetime, timezone
from typing import Optional

from app.database import engine
from app.models import Photo, Task, PlaceSummary


@click.group()
def task():
    """Task processing commands"""
    pass


def create_task(
    db: Session, name: str, task_type: str, total: Optional[int] = None
) -> Task:
    """Create a new task record"""
    task = Task(
        name=name,
        task_type=task_type,
        status="pending",
        progress=0,
        total=total,
        processed=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_progress(
    db: Session, task: Task, processed: int, total: Optional[int] = None
):
    """Update task progress"""
    task.processed = processed
    if total is not None:
        task.total = total
    if task.total and task.total > 0:
        task.progress = int((processed / task.total) * 100)
    db.add(task)
    db.commit()


def mark_task_running(db: Session, task: Task):
    """Mark task as running"""
    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
    db.add(task)
    db.commit()


def mark_task_completed(db: Session, task: Task):
    """Mark task as completed"""
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.progress = 100
    db.add(task)
    db.commit()


def mark_task_failed(db: Session, task: Task, error_message: str):
    """Mark task as failed"""
    task.status = "failed"
    task.completed_at = datetime.now(timezone.utc)
    task.error_message = error_message
    db.add(task)
    db.commit()


@task.command("lookup-places")
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of photos to process",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be processed without making changes",
)
def lookup_places(limit: Optional[int], dry_run: bool):
    """
    Look up place information for photos with coordinates but no place data.

    Uses python-gazetteer to reverse geocode latitude/longitude coordinates
    and populate the place field with location information.
    """
    try:
        from gazetteer import GeoNames
    except ImportError:
        click.echo(
            "Error: python-gazetteer not installed. "
            "Install it with: pip install python-gazetteer",
            err=True,
        )
        return 1

    click.echo("Looking up place information for photos...")

    with Session(engine) as db:
        # Find photos with coordinates but no place data
        query = select(Photo).where(
            and_(
                Photo.latitude.isnot(None),
                Photo.longitude.isnot(None),
                or_(
                    Photo.place.is_(None),
                    Photo.place == {},
                ),
            )
        )

        if limit:
            query = query.limit(limit)

        photos = db.exec(query).all()

        if not photos:
            click.echo("No photos found that need place lookup")
            return 0

        click.echo(f"Found {len(photos)} photos to process")

        if dry_run:
            click.echo("\nDry run - would process the following photos:")
            for photo in photos[:10]:
                click.echo(
                    f"  - {photo.uuid}: ({photo.latitude}, {photo.longitude})"
                )
            if len(photos) > 10:
                click.echo(f"  ... and {len(photos) - 10} more")
            return 0

        # Create task
        task_record = create_task(
            db, "Lookup place information", "lookup_places", len(photos)
        )
        mark_task_running(db, task_record)

        click.echo(f"\nTask created with ID: {task_record.id}")

        # Initialize gazetteer
        try:
            geo = GeoNames()
        except Exception as e:
            error_msg = f"Failed to initialize GeoNames: {e}"
            click.echo(f"Error: {error_msg}", err=True)
            mark_task_failed(db, task_record, error_msg)
            return 1

        processed = 0
        errors = 0

        for photo in photos:
            try:
                # Reverse geocode the coordinates
                result = geo.reverse(photo.latitude, photo.longitude)

                if result:
                    # Extract place information
                    place_data = {
                        "name": result.get("name", ""),
                        "country": result.get("countryName", ""),
                        "country_code": result.get("countryCode", ""),
                        "admin1": result.get("adminName1", ""),  # State/Province
                        "admin2": result.get("adminName2", ""),  # County
                        "latitude": photo.latitude,
                        "longitude": photo.longitude,
                    }

                    # Update photo
                    photo.place = place_data
                    db.add(photo)

                    processed += 1

                    if processed % 10 == 0:
                        db.commit()
                        update_task_progress(db, task_record, processed)
                        click.echo(f"Processed {processed}/{len(photos)} photos...")
                else:
                    errors += 1
                    click.echo(
                        f"Warning: No place found for photo {photo.uuid} "
                        f"at ({photo.latitude}, {photo.longitude})",
                        err=True,
                    )

            except Exception as e:
                errors += 1
                click.echo(f"Error processing photo {photo.uuid}: {e}", err=True)

        # Final commit and task update
        db.commit()
        mark_task_completed(db, task_record)

        click.echo(f"\nCompleted!")
        click.echo(f"  Processed: {processed} photos")
        if errors > 0:
            click.echo(f"  Errors: {errors}")

        return 0


@task.command("update-place-summary")
@click.option(
    "--rebuild",
    is_flag=True,
    help="Rebuild the entire summary table from scratch",
)
def update_place_summary(rebuild: bool):
    """
    Update the place summary table with aggregated data from photos.

    This creates/updates a summary of all places with photo counts and date ranges,
    enabling faster map queries without scanning all photos.
    """
    click.echo("Updating place summary table...")

    with Session(engine) as db:
        # Clear existing data if rebuilding
        if rebuild:
            click.echo("Clearing existing summary data...")
            db.query(PlaceSummary).delete()
            db.commit()

        # Get all photos with place data
        query = select(Photo).where(
            and_(
                Photo.place.isnot(None),
                Photo.place != {},
            )
        )

        photos = db.exec(query).all()

        if not photos:
            click.echo("No photos found with place data")
            return 0

        click.echo(f"Found {len(photos)} photos with place data")

        # Create task
        task_record = create_task(
            db, "Update place summary", "update_place_summary", len(photos)
        )
        mark_task_running(db, task_record)

        click.echo(f"Task created with ID: {task_record.id}")

        # Aggregate data by place name
        place_aggregates = {}

        for photo in photos:
            if not photo.place:
                continue

            # Extract place name (use country if no specific name)
            place_name = photo.place.get("name") or photo.place.get("country") or "Unknown"

            if place_name not in place_aggregates:
                place_aggregates[place_name] = {
                    "place_name": place_name,
                    "latitude": photo.latitude,
                    "longitude": photo.longitude,
                    "photo_count": 0,
                    "first_photo_date": photo.date,
                    "last_photo_date": photo.date,
                    "country": photo.place.get("country"),
                    "state_province": photo.place.get("admin1"),
                    "city": photo.place.get("admin2") or photo.place.get("name"),
                    "place_data": photo.place,
                }

            agg = place_aggregates[place_name]
            agg["photo_count"] += 1

            # Update date range
            if photo.date < agg["first_photo_date"]:
                agg["first_photo_date"] = photo.date
            if photo.date > agg["last_photo_date"]:
                agg["last_photo_date"] = photo.date

        click.echo(f"Aggregated data for {len(place_aggregates)} unique places")

        # Update or create PlaceSummary records
        processed = 0
        for place_name, data in place_aggregates.items():
            try:
                # Check if record exists
                existing = db.exec(
                    select(PlaceSummary).where(
                        PlaceSummary.place_name == place_name
                    )
                ).first()

                if existing:
                    # Update existing record
                    existing.latitude = data["latitude"]
                    existing.longitude = data["longitude"]
                    existing.photo_count = data["photo_count"]
                    existing.first_photo_date = data["first_photo_date"]
                    existing.last_photo_date = data["last_photo_date"]
                    existing.country = data["country"]
                    existing.state_province = data["state_province"]
                    existing.city = data["city"]
                    existing.place_data = data["place_data"]
                    existing.updated_at = datetime.now(timezone.utc)
                    db.add(existing)
                else:
                    # Create new record
                    summary = PlaceSummary(**data)
                    db.add(summary)

                processed += 1

                if processed % 50 == 0:
                    db.commit()
                    update_task_progress(db, task_record, processed, len(place_aggregates))
                    click.echo(f"Processed {processed}/{len(place_aggregates)} places...")

            except Exception as e:
                click.echo(f"Error processing place {place_name}: {e}", err=True)

        # Final commit and task update
        db.commit()
        mark_task_completed(db, task_record)

        click.echo(f"\nCompleted!")
        click.echo(f"  Updated: {processed} place summaries")

        return 0


@task.command("list")
@click.option(
    "--status",
    type=click.Choice(["pending", "running", "completed", "failed", "all"]),
    default="all",
    help="Filter tasks by status",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Limit the number of tasks to show",
)
def list_tasks(status: str, limit: int):
    """List all tasks"""
    with Session(engine) as db:
        query = select(Task).order_by(Task.created_at.desc())

        if status != "all":
            query = query.where(Task.status == status)

        query = query.limit(limit)

        tasks = db.exec(query).all()

        if not tasks:
            click.echo("No tasks found")
            return

        click.echo(f"\nFound {len(tasks)} tasks:")
        click.echo("-" * 80)

        for task_record in tasks:
            status_icon = {
                "pending": "⏳",
                "running": "▶️",
                "completed": "✅",
                "failed": "❌",
            }.get(task_record.status, "❓")

            click.echo(f"{status_icon} Task #{task_record.id}: {task_record.name}")
            click.echo(f"   Type: {task_record.task_type}")
            click.echo(f"   Status: {task_record.status}")
            if task_record.total:
                click.echo(
                    f"   Progress: {task_record.processed}/{task_record.total} "
                    f"({task_record.progress}%)"
                )
            else:
                click.echo(f"   Processed: {task_record.processed}")
            click.echo(f"   Created: {task_record.created_at}")
            if task_record.completed_at:
                click.echo(f"   Completed: {task_record.completed_at}")
            if task_record.error_message:
                click.echo(f"   Error: {task_record.error_message}")
            click.echo()
