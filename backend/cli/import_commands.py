"""Photo import CLI commands"""

import click
import os
import json
import mimetypes
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import uuid as uuid_module
import dateutil
from sqlalchemy.orm import Session
from sqlmodel import select
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from ulid import ULID


from app.database import SessionLocal
from app.models import User, Library, Photo, Version


@click.command(name="import")
@click.option("--username", required=True, help="Username of the photo owner")
@click.option("--library-id", type=int, help="Library ID (optional)")
@click.option(
    "--library-name", help="Library name (optional, creates if doesn't exist)"
)
@click.option(
    "--folder",
    required=True,
    type=click.Path(exists=True),
    help="Folder to import from",
)
@click.option(
    "--sidecar-format",
    type=click.Choice(["json", "xmp"]),
    default="json",
    help="Sidecar file format",
)
@click.option(
    "--s3-bucket", help="S3 bucket name for uploads (automatically enables S3 upload)"
)
@click.option("--s3-prefix", help="S3 key prefix (default: username/library_name)")
@click.option("--dry-run", is_flag=True, help="Dry run - don't actually import")
def import_photos(
    username: str,
    library_id: Optional[int],
    library_name: Optional[str],
    folder: str,
    sidecar_format: str,
    s3_bucket: Optional[str],
    s3_prefix: Optional[str],
    dry_run: bool,
):
    """Import photos from a folder with sidecar metadata"""
    db: Session = SessionLocal()

    try:
        # Get user
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return

        # Get or create library
        library = None
        if library_id:
            library = db.exec(select(Library).where(Library.id == library_id)).first()
            if not library:
                click.echo(f"Error: Library {library_id} not found", err=True)
                return
        elif library_name:
            library = db.exec(
                select(Library).where(
                    Library.owner_id == user.id, Library.name == library_name
                )
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

        # Setup S3 if bucket is specified (automatically enables upload)
        s3_client = None
        if s3_bucket:
            try:
                import boto3

                s3_client = boto3.client("s3")
                if not s3_prefix:
                    s3_prefix = f"{username}/{library.name if library else 'default'}"
                click.echo(f"✓ S3 uploads enabled: s3://{s3_bucket}/{s3_prefix}")

                # Test S3 connection
                try:
                    s3_client.head_bucket(Bucket=s3_bucket)
                except Exception as e:
                    click.echo(
                        f"Warning: Could not verify S3 bucket access: {str(e)}",
                        err=True,
                    )
            except ImportError:
                click.echo(
                    "Error: boto3 not installed. Install with: pip install boto3",
                    err=True,
                )
                return
            except Exception as e:
                click.echo(f"Error: Failed to initialize S3 client: {str(e)}", err=True)
                return

        # Import photos
        folder_path = Path(folder)
        imported = 0
        skipped = 0
        errors = 0

        # Find all image files
        image_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".heic",
            ".heif",
            ".tiff",
            ".raw",
            ".dng",
            ".mov",
            ".mp4",
        }
        image_files = [
            f for f in folder_path.rglob("*") if f.suffix.lower() in image_extensions
        ]

        click.echo(f"\nFound {len(image_files)} image files to process")

        with click.progressbar(image_files, label="Importing photos") as files:
            for image_file in files:
                try:
                    # Extract EXIF data from the image itself
                    exif_data = extract_exif_data(image_file)

                    # Look for sidecar file
                    sidecar_path = None
                    if sidecar_format == "json":
                        sidecar_path = image_file.with_suffix(
                            image_file.suffix + ".json"
                        )
                        if not sidecar_path.exists():
                            sidecar_path = image_file.with_suffix(".json")
                    elif sidecar_format == "xmp":
                        sidecar_path = image_file.with_suffix(".xmp")

                    # Parse metadata from sidecar files
                    metadata = {}
                    if sidecar_path and sidecar_path.exists():
                        metadata = parse_sidecar(sidecar_path, sidecar_format)

                    for meta_json_path in [
                        image_file.parent / "meta.json",
                        image_file.parent / "metadata.json",
                    ]:
                        # Parse and merge meta.json if it exists
                        if meta_json_path.exists():
                            meta_json_data = parse_meta_json(meta_json_path)
                            # Merge meta.json data, giving priority to sidecar data
                            for key, value in meta_json_data.items():
                                if key not in metadata:
                                    metadata[key] = value

                    # Add EXIF data to metadata
                    if exif_data:
                        # If there's already EXIF in metadata (from sidecar), merge them
                        if "exif" in metadata and isinstance(metadata["exif"], dict):
                            # Prefer sidecar EXIF but add any missing fields from extracted EXIF
                            for key, value in exif_data.items():
                                if key not in metadata["exif"]:
                                    metadata["exif"][key] = value
                        else:
                            metadata["exif"] = exif_data

                    # Create photo record
                    photo_data = create_photo_from_file(
                        image_file,
                        metadata,
                        library,
                        user.id,
                        s3_client,
                        s3_bucket,
                        s3_prefix,
                        dry_run,
                    )

                    if not dry_run:
                        # Check if photo already exists
                        existing = db.exec(
                            select(Photo).where(Photo.uuid == photo_data["uuid"])
                        ).first()
                        if existing:
                            skipped += 1
                            continue

                        # Create photo
                        db_photo = Photo(**photo_data)
                        db.add(db_photo)
                        db.flush()  # Flush to get the photo ID before creating version

                        # Create version record if it doesn't exist
                        try:
                            existing_version = db.exec(
                                select(Version).where(
                                    Version.photo_uuid == db_photo.uuid,
                                    Version.version == "original",
                                )
                            ).first()
                            if not existing_version:
                                # Determine version type
                                content_type = photo_data.get("content_type", "")
                                version_type = (
                                    "photo"
                                    if content_type.startswith("image/")
                                    else "video"
                                )

                                # Get S3 path or use empty string if not uploaded to S3
                                s3_path = (
                                    photo_data.get("s3_key_path")
                                    or photo_data.get("s3_original_path")
                                    or ""
                                )

                                version_data = {
                                    "photo_uuid": db_photo.uuid,
                                    "version": "original",
                                    "s3_path": s3_path,  # Required field, empty string if no S3
                                    "filename": photo_data.get("original_filename"),
                                    "width": photo_data.get("width"),
                                    "height": photo_data.get("height"),
                                    "size": photo_data.get("file_size"),
                                    "type": version_type,
                                }
                                db_version = Version(**version_data)
                                db.add(db_version)
                                db.flush()  # Flush to ensure version is added
                                click.echo(
                                    f"✓ Created version for {photo_data.get('original_filename', 'photo')}"
                                )
                            else:
                                click.echo(
                                    f"⚠ Version already exists for {photo_data.get('original_filename', 'photo')}"
                                )
                        except Exception as e:
                            click.echo(
                                f"\nError creating version for {photo_data.get('original_filename', 'photo')}: {str(e)}",
                                err=True,
                            )
                            # Print full traceback for debugging
                            import traceback

                            click.echo(traceback.format_exc(), err=True)

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


def extract_exif_data(image_path: Path) -> Dict[str, Any]:
    """Extract EXIF data from an image file using Pillow"""
    # EXIF constants
    GPS_IFD_TAG = 0x8825  # GPS IFD tag for GPS information
    FLASH_FIRED_BIT = 0x1  # Bit 0 indicates if flash was fired

    exif_data = {}

    try:
        with Image.open(image_path) as img:
            exif = img.getexif()

            if exif is None:
                return exif_data

            # Extract common EXIF fields
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)

                # Convert value to serializable format
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore")
                    except (UnicodeDecodeError, AttributeError):
                        value = str(value)

                exif_data[tag_name] = value

            # Extract GPS data if available
            gps_info = exif.get_ifd(GPS_IFD_TAG)
            if gps_info:
                gps_data = {}
                for tag_id, value in gps_info.items():
                    tag_name = GPSTAGS.get(tag_id, tag_id)
                    gps_data[tag_name] = value

                if gps_data:
                    exif_data["GPS"] = gps_data

            # Extract useful fields in a structured format matching Django model
            structured_exif = {}

            if "Make" in exif_data:
                structured_exif["camera_make"] = exif_data["Make"]
            if "Model" in exif_data:
                structured_exif["camera_model"] = exif_data["Model"]
            if "LensModel" in exif_data:
                structured_exif["lens_model"] = exif_data["LensModel"]

            # Exposure settings
            if "ExposureTime" in exif_data:
                # Handle tuple format (numerator, denominator)
                exp_time = exif_data["ExposureTime"]
                if isinstance(exp_time, tuple) and len(exp_time) == 2:
                    structured_exif["shutter_speed"] = exp_time[0] / exp_time[1]
                else:
                    structured_exif["shutter_speed"] = float(exp_time)

            if "FNumber" in exif_data:
                f_num = exif_data["FNumber"]
                if isinstance(f_num, tuple) and len(f_num) == 2:
                    structured_exif["aperture"] = f_num[0] / f_num[1]
                else:
                    structured_exif["aperture"] = float(f_num)

            # ISO
            if "ISOSpeedRatings" in exif_data:
                structured_exif["iso"] = exif_data["ISOSpeedRatings"]
            elif "ISO" in exif_data:
                structured_exif["iso"] = exif_data["ISO"]

            # Focal length
            if "FocalLength" in exif_data:
                focal = exif_data["FocalLength"]
                if isinstance(focal, tuple) and len(focal) == 2:
                    structured_exif["focal_length"] = focal[0] / focal[1]
                else:
                    structured_exif["focal_length"] = float(focal)

            # Flash
            if "Flash" in exif_data:
                flash_value = exif_data["Flash"]
                # Flash fired if bit 0 is set
                structured_exif["flash_fired"] = (
                    bool(flash_value & FLASH_FIRED_BIT)
                    if isinstance(flash_value, int)
                    else False
                )

            # White balance
            if "WhiteBalance" in exif_data:
                structured_exif["white_balance"] = exif_data["WhiteBalance"]

            # Metering mode
            if "MeteringMode" in exif_data:
                structured_exif["metering_mode"] = exif_data["MeteringMode"]

            # Exposure bias
            if "ExposureBiasValue" in exif_data:
                bias = exif_data["ExposureBiasValue"]
                if isinstance(bias, tuple) and len(bias) == 2:
                    structured_exif["exposure_bias"] = bias[0] / bias[1]
                else:
                    structured_exif["exposure_bias"] = float(bias)

            # Add raw EXIF data for reference
            structured_exif["_raw"] = exif_data

            return structured_exif

    except Exception as e:
        # If we can't read EXIF, just return empty dict
        click.echo(
            f"\nWarning: Could not extract EXIF from {image_path.name}: {str(e)}",
            err=True,
        )
        return exif_data

    return exif_data


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
                "original_filename": data.get("original_filename")
                or data.get("filename"),
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


def parse_meta_json(meta_json_path: Path) -> Dict[str, Any]:
    """Parse meta.json file for arbitrary metadata

    This function reads a meta.json file and returns all metadata as-is.
    Any metadata found will be stored in the 'fields' column of the Photo model.
    """
    try:
        with open(meta_json_path, "r") as f:
            data = json.load(f)

            # If the JSON contains a 'fields' key, use that directly
            # Otherwise, store the entire JSON in fields
            if isinstance(data, dict):
                # Check if this looks like PhotoSafe metadata (has known fields)
                known_fields = {
                    "uuid",
                    "masterFingerprint",
                    "original_filename",
                    "date",
                    "title",
                    "description",
                    "keywords",
                    "labels",
                    "persons",
                    "favorite",
                    "hidden",
                    "latitude",
                    "longitude",
                    "exif",
                }

                # If it has known fields, parse them normally
                if any(field in data for field in known_fields):
                    return data

                # Otherwise, treat it as arbitrary metadata
                return {"fields": data}

            return {}
    except Exception as e:
        click.echo(
            f"\nWarning: Could not parse meta.json at {meta_json_path}: {str(e)}",
            err=True,
        )
        return {}


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_file_md5(file_path: Path) -> str:
    """Calculate MD5 hash of a file (for S3 ETag comparison)"""
    md5_hash = hashlib.md5()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()


def extract_date_from_timestamp(d):
    if d:
        dateutil.parse(d)


def extract_date_from_exif(exif_data: Dict[str, Any]) -> Optional[datetime]:
    """Extract date from EXIF data, trying DateTimeOriginal first, then DateTime"""
    if not exif_data:
        return None

    # Check structured EXIF first
    if isinstance(exif_data, dict):
        # Try DateTimeOriginal first (most accurate)
        if "DateTimeOriginal" in exif_data:
            date_str = exif_data["DateTimeOriginal"]
            if isinstance(date_str, str):
                try:
                    # EXIF DateTime format: "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    pass

        # Fall back to DateTime
        if "DateTime" in exif_data:
            date_str = exif_data["DateTime"]
            if isinstance(date_str, str):
                try:
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                except ValueError:
                    pass

        # Check _raw EXIF data
        if "_raw" in exif_data and isinstance(exif_data["_raw"], dict):
            raw_exif = exif_data["_raw"]
            if "DateTimeOriginal" in raw_exif:
                date_str = raw_exif["DateTimeOriginal"]
                if isinstance(date_str, str):
                    try:
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        pass

            if "DateTime" in raw_exif:
                date_str = raw_exif["DateTime"]
                if isinstance(date_str, str):
                    try:
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        pass

    return None


def create_photo_from_file(
    file_path: Path,
    metadata: Dict[str, Any],
    library: Optional[Library],
    owner_id: int,
    s3_client,
    s3_bucket: Optional[str],
    s3_prefix: Optional[str],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Create photo data dictionary from file and metadata"""

    # Get file info
    file_stat = file_path.stat()
    file_size = file_stat.st_size

    # Extract date for ULID generation (priority: EXIF -> filesystem)
    date_for_ulid = None

    # Try to get date from EXIF first
    exif_data = metadata.get("exif")
    if exif_data:
        date_for_ulid = extract_date_from_exif(exif_data)

    # Fall back to filesystem modification time
    if not date_for_ulid:
        for key in ("created_at", "createdAt"):
            if dt := metadata.get(key):
                date_for_ulid = extract_date_from_timestamp(dt)
        date_for_ulid = datetime.fromtimestamp(file_stat.st_mtime)

    # Generate UUID or ULID if not in metadata
    photo_uuid = metadata.get("uuid")
    if not photo_uuid:
        # Generate ULID based on the date and convert to UUID
        ulid_obj = ULID.from_datetime(date_for_ulid)
        photo_uuid = str(ulid_obj.to_uuid())

    # Detect MIME type
    suffix = file_path.suffix.lower()
    content_type = mimetypes.types_map.get(suffix)
    if suffix == ".heic":
        content_type = "image/heic"
    if not content_type:
        content_type = "application/octet-stream"

    # Upload to S3 if configured
    s3_key_path = None
    if s3_client and s3_bucket and not dry_run:
        if not s3_prefix:
            click.echo(f"\nError: S3 prefix not set for {file_path.name}", err=True)
        else:
            s3_key = f"{s3_prefix}/{photo_uuid}/{file_path.name}"
            try:
                # Ensure file exists before uploading
                if not file_path.exists():
                    click.echo(f"\nError: File does not exist: {file_path}", err=True)
                else:
                    # Check if file already exists in S3 and compare hash
                    file_needs_upload = True
                    try:
                        # Check if object exists
                        response = s3_client.head_object(Bucket=s3_bucket, Key=s3_key)
                        s3_etag = response.get("ETag", "").strip('"')

                        # Calculate local file MD5 (S3 ETag is MD5 for single-part uploads)
                        local_md5 = calculate_file_md5(file_path)

                        # Compare hashes
                        if s3_etag == local_md5:
                            file_needs_upload = False
                            # File exists in S3, set s3_key_path even though we didn't upload
                            s3_key_path = s3_key
                            click.echo(
                                f"✓ File already exists in S3 with matching hash: {file_path.name}"
                            )
                        else:
                            click.echo(
                                f"⚠ File exists in S3 but hash differs, re-uploading: {file_path.name}"
                            )
                    except Exception as e:
                        # Check if it's a ClientError (file doesn't exist)
                        error_code = None
                        if hasattr(e, "response"):
                            error_code = e.response.get("Error", {}).get("Code", "")

                        if error_code == "404" or "Not Found" in str(e):
                            # File doesn't exist, proceed with upload
                            pass
                        else:
                            # Other error, log but proceed
                            click.echo(
                                f"Warning: Could not check S3 object: {str(e)}",
                                err=True,
                            )

                    # Upload if needed
                    if file_needs_upload:
                        s3_client.upload_file(
                            str(file_path),
                            s3_bucket,
                            s3_key,
                            ExtraArgs={"ContentType": content_type},
                        )
                        click.echo(f"✓ Uploaded to S3: s3://{s3_bucket}/{s3_key}")
                        # Set s3_key_path after successful upload
                        s3_key_path = s3_key
            except Exception as e:
                # If upload fails, continue without S3 path but show error
                click.echo(
                    f"\nError: S3 upload failed for {file_path.name}: {str(e)}",
                    err=True,
                )

    # Parse date (use the date we already extracted for ULID if available)
    photo_date = metadata.get("date")
    if photo_date and isinstance(photo_date, str):
        try:
            photo_date = datetime.fromisoformat(photo_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            photo_date = date_for_ulid if date_for_ulid else datetime.utcnow()
    elif not photo_date:
        # Use the date we extracted for ULID (EXIF or filesystem)
        photo_date = date_for_ulid

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
        "masterFingerprint",
        "title",
        "description",
        "keywords",
        "labels",
        "persons",
        "favorite",
        "hidden",
        "latitude",
        "longitude",
        "isphoto",
        "ismovie",
        "burst",
        "live_photo",
        "portrait",
        "screenshot",
        "slow_mo",
        "time_lapse",
        "hdr",
        "selfie",
        "panorama",
        "uti",
        "width",
        "height",
        "orientation",
        "exif",
        "place",
        "score",
        "search_info",
        "faces",
        "fields",
    ]:
        if key in metadata:
            photo_data[key] = metadata[key]

    # If masterFingerprint is null, use the hash of the file
    if not photo_data.get("masterFingerprint"):
        photo_data["masterFingerprint"] = calculate_file_hash(file_path)

    return photo_data
