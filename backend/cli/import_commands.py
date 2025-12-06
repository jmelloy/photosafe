"""Photo import CLI commands"""

import click
import os
import json
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import uuid as uuid_module
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Library, Photo, Version


@click.command(name="import")
@click.option("--username", required=True, help="Username of the photo owner")
@click.option("--library-id", type=int, help="Library ID (optional)")
@click.option("--library-name", help="Library name (optional, creates if doesn't exist)")
@click.option("--folder", required=True, type=click.Path(exists=True), help="Folder to import from")
@click.option("--sidecar-format", type=click.Choice(["json", "xmp"]), default="json", help="Sidecar file format")
@click.option("--s3-bucket", help="S3 bucket name for uploads")
@click.option("--s3-prefix", help="S3 key prefix (default: username/library_name)")
@click.option("--upload-to-s3", is_flag=True, help="Upload photos to S3")
@click.option("--dry-run", is_flag=True, help="Dry run - don't actually import")
def import_photos(
    username: str,
    library_id: Optional[int],
    library_name: Optional[str],
    folder: str,
    sidecar_format: str,
    s3_bucket: Optional[str],
    s3_prefix: Optional[str],
    upload_to_s3: bool,
    dry_run: bool,
):
    """Import photos from a folder with sidecar metadata"""
    db: Session = SessionLocal()
    
    try:
        # Get user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return

        # Get or create library
        library = None
        if library_id:
            library = db.query(Library).filter(Library.id == library_id).first()
            if not library:
                click.echo(f"Error: Library {library_id} not found", err=True)
                return
        elif library_name:
            library = db.query(Library).filter(
                Library.owner_id == user.id,
                Library.name == library_name
            ).first()
            if not library and not dry_run:
                library = Library(
                    name=library_name,
                    path=folder,
                    owner_id=user.id,
                )
                db.add(library)
                db.commit()
                db.refresh(library)
                click.echo(f"✓ Created new library: {library_name} (ID: {library.id})")

        # Setup S3 if needed
        s3_client = None
        if upload_to_s3:
            if not s3_bucket:
                click.echo("Error: --s3-bucket required when using --upload-to-s3", err=True)
                return
            try:
                import boto3
                s3_client = boto3.client("s3")
                if not s3_prefix:
                    s3_prefix = f"{username}/{library.name if library else 'default'}"
                click.echo(f"✓ S3 uploads enabled: s3://{s3_bucket}/{s3_prefix}")
            except ImportError:
                click.echo("Error: boto3 not installed. Install with: pip install boto3", err=True)
                return

        # Import photos
        folder_path = Path(folder)
        imported = 0
        skipped = 0
        errors = 0

        # Find all image files
        image_extensions = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".raw", ".dng", ".mov", ".mp4"}
        image_files = [f for f in folder_path.rglob("*") if f.suffix.lower() in image_extensions]

        click.echo(f"\nFound {len(image_files)} image files to process")
        
        with click.progressbar(image_files, label="Importing photos") as files:
            for image_file in files:
                try:
                    # Look for sidecar file
                    sidecar_path = None
                    if sidecar_format == "json":
                        sidecar_path = image_file.with_suffix(image_file.suffix + ".json")
                        if not sidecar_path.exists():
                            sidecar_path = image_file.with_suffix(".json")
                    elif sidecar_format == "xmp":
                        sidecar_path = image_file.with_suffix(".xmp")

                    # Parse metadata
                    metadata = {}
                    if sidecar_path and sidecar_path.exists():
                        metadata = parse_sidecar(sidecar_path, sidecar_format)

                    # Create photo record
                    photo_data = create_photo_from_file(
                        image_file, metadata, library, user.id, s3_client, s3_bucket, s3_prefix
                    )

                    if not dry_run:
                        # Check if photo already exists
                        existing = db.query(Photo).filter(Photo.uuid == photo_data["uuid"]).first()
                        if existing:
                            skipped += 1
                            continue

                        # Create photo
                        db_photo = Photo(**photo_data)
                        db.add(db_photo)
                        db.commit()
                        imported += 1
                    else:
                        imported += 1

                except Exception as e:
                    errors += 1
                    click.echo(f"\nError processing {image_file}: {str(e)}", err=True)

        click.echo(f"\n✓ Import complete:")
        click.echo(f"  Imported: {imported}")
        click.echo(f"  Skipped:  {skipped}")
        click.echo(f"  Errors:   {errors}")
        if dry_run:
            click.echo(f"  (Dry run - no changes made)")

    except Exception as e:
        db.rollback()
        click.echo(f"Error during import: {str(e)}", err=True)
    finally:
        db.close()


def parse_sidecar(sidecar_path: Path, format: str) -> Dict[str, Any]:
    """Parse sidecar file and return metadata dictionary"""
    metadata = {}
    
    if format == "json":
        with open(sidecar_path, "r") as f:
            data = json.load(f)
            
            # Map Apple Photos JSON format to PhotoSafe schema
            metadata = {
                "uuid": data.get("uuid"),
                "masterFingerprint": data.get("fingerprint"),
                "original_filename": data.get("original_filename") or data.get("filename"),
                "date": data.get("date") or data.get("date_original"),
                "title": data.get("title"),
                "description": data.get("description"),
                "keywords": data.get("keywords", []),
                "labels": data.get("labels", []),
                "persons": data.get("persons", []),
                "favorite": data.get("favorite", False),
                "hidden": data.get("hidden", False),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "isphoto": data.get("isphoto", True),
                "ismovie": data.get("ismovie", False),
                "burst": data.get("burst", False),
                "live_photo": data.get("live_photo", False),
                "portrait": data.get("portrait", False),
                "screenshot": data.get("screenshot", False),
                "slow_mo": data.get("slow_mo", False),
                "time_lapse": data.get("time_lapse", False),
                "hdr": data.get("hdr", False),
                "selfie": data.get("selfie", False),
                "panorama": data.get("panorama", False),
                "uti": data.get("uti"),
                "width": data.get("width") or data.get("original_width"),
                "height": data.get("height") or data.get("original_height"),
                "orientation": data.get("orientation"),
                "exif": data.get("exif_info"),
                "place": data.get("place"),
                "score": data.get("score"),
                "search_info": data.get("search_info"),
                "faces": data.get("face_info"),
            }
            
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
    
    elif format == "xmp":
        # Basic XMP parsing (could be enhanced with python-xmp-toolkit)
        # For now, just extract basic metadata
        import xml.etree.ElementTree as ET
        tree = ET.parse(sidecar_path)
        root = tree.getroot()
        
        # Extract basic fields from XMP
        # This is a simplified implementation
        metadata = {}
    
    return metadata


def create_photo_from_file(
    file_path: Path,
    metadata: Dict[str, Any],
    library: Optional[Library],
    owner_id: int,
    s3_client,
    s3_bucket: Optional[str],
    s3_prefix: Optional[str],
) -> Dict[str, Any]:
    """Create photo data dictionary from file and metadata"""
    
    # Generate UUID if not in metadata
    photo_uuid = metadata.get("uuid", str(uuid_module.uuid4()))
    
    # Get file info
    file_stat = file_path.stat()
    file_size = file_stat.st_size
    
    # Detect MIME type
    suffix = file_path.suffix.lower()
    content_type = mimetypes.types_map.get(suffix)
    if suffix == ".heic":
        content_type = "image/heic"
    if not content_type:
        content_type = "application/octet-stream"
    
    # Upload to S3 if configured
    s3_key_path = None
    if s3_client and s3_bucket:
        s3_key = f"{s3_prefix}/{photo_uuid}/{file_path.name}"
        try:
            s3_client.upload_file(
                str(file_path),
                s3_bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type}
            )
            s3_key_path = s3_key
        except Exception as e:
            # If upload fails, continue without S3 path
            click.echo(f"\nWarning: S3 upload failed for {file_path.name}: {str(e)}", err=True)
    
    # Parse date
    photo_date = metadata.get("date")
    if photo_date and isinstance(photo_date, str):
        try:
            photo_date = datetime.fromisoformat(photo_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            photo_date = datetime.utcnow()
    elif not photo_date:
        # Use file modification time
        photo_date = datetime.fromtimestamp(file_stat.st_mtime)
    
    # Build photo data
    photo_data = {
        "uuid": photo_uuid,
        "owner_id": owner_id,
        "library_id": library.id if library else None,
        "library": library.name if library else None,
        "original_filename": metadata.get("original_filename", file_path.name),
        "date": photo_date,
        "file_size": file_size,
        "content_type": content_type,
    }
    
    # Add S3 path if uploaded
    if s3_key_path:
        photo_data["s3_original_path"] = s3_key_path
        photo_data["s3_key_path"] = s3_key_path
    
    # Merge metadata
    for key in [
        "masterFingerprint", "title", "description", "keywords", "labels",
        "persons", "favorite", "hidden", "latitude", "longitude", "isphoto",
        "ismovie", "burst", "live_photo", "portrait", "screenshot", "slow_mo",
        "time_lapse", "hdr", "selfie", "panorama", "uti", "width", "height",
        "orientation", "exif", "place", "score", "search_info", "faces",
    ]:
        if key in metadata:
            photo_data[key] = metadata[key]
    
    # Serialize JSON fields for SQLite compatibility
    for field in ["keywords", "labels", "persons", "faces", "place", "exif", "score", "search_info"]:
        if field in photo_data and photo_data[field] is not None:
            if isinstance(photo_data[field], (list, dict)):
                photo_data[field] = json.dumps(photo_data[field])
    
    return photo_data
