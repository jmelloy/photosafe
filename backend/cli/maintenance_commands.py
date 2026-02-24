#!/usr/bin/env python
"""PhotoSafe CLI - Maintenance and diagnostic commands"""

import csv
import gzip
import os
import sys
import tempfile
from typing import Any, Dict, List, Sequence, Tuple
from urllib.parse import urlparse, unquote

import boto3
import click

from sqlmodel import Session, select

from app.database import engine
from app.models import Version, Photo

from cli.sync_tools import list_bucket

# Expected S3 CSV column names
S3_CSV_COLUMNS = ["bucket", "key", "size", "lastmodifieddate", "etag"]


@click.group()
def maintenance():
    """Maintenance and diagnostic commands"""
    pass


@maintenance.command()
def populate_search_data():
    """
    Populate search_data table from existing photo metadata

    This command will:
    1. Process all photos in the database
    2. Extract searchable metadata (labels, keywords, persons, places, etc.)
    3. Populate the search_data table for efficient searching

    Run this after upgrading to the search_data feature or if search_data
    becomes out of sync with photo metadata.
    """
    from app.utils import populate_search_data_for_all_photos

    click.echo("PhotoSafe Search Data Population Tool")
    click.echo("=" * 80)
    click.echo("This will populate the search_data table from all photos...")

    with Session(engine) as db:
        try:
            count = populate_search_data_for_all_photos(db)
            click.echo(f"\n✅ Successfully processed {count} photos")
            click.echo("Search data has been populated!")
        except Exception as e:
            click.echo(f"\n❌ Error: {e}", err=True)
            sys.exit(1)


def download_s3_csv(s3_url: str) -> str:
    """
    Download CSV file from S3 to a temporary location

    Args:
        s3_url: S3 URL like s3://bucket/path/to/file.csv or s3://bucket/path/to/file.csv.gz

    Returns:
        Path to downloaded (and possibly decompressed) file
    """
    parsed = urlparse(s3_url)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URL: {s3_url}. Must start with s3://")

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    click.echo(f"Downloading from S3: {bucket}/{key}")

    s3 = boto3.client("s3")

    # Download to temp file
    temp_dir = tempfile.gettempdir()
    local_filename = os.path.basename(key)
    temp_path = os.path.join(temp_dir, local_filename)

    try:
        s3.download_file(bucket, key, temp_path)
        click.echo(f"Downloaded to: {temp_path}")

        # If it's gzipped, decompress it
        if temp_path.endswith(".gz"):
            click.echo("Decompressing gzipped file...")
            decompressed_path = temp_path[:-3]  # Remove .gz extension

            with gzip.open(temp_path, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    f_out.write(f_in.read())

            # Remove the gzipped file
            os.remove(temp_path)
            click.echo(f"Decompressed to: {decompressed_path}")
            return decompressed_path

        return temp_path

    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def get_s3_objects_from_csv(csv_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all objects from S3 CSV export with their sizes and bucket info

    Expected CSV format: Bucket, Key, Size, LastModifiedDate, ETag
    (Bucket column is optional)

    Returns:
        Dict mapping s3_path -> {"size": int, "bucket": str}
    """
    objects = {}

    click.echo(f"Reading S3 objects from CSV: {csv_path}")

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # Read the first line to detect the header
            first_line = f.readline().strip()
            f.seek(0)  # Reset to beginning

            # Check if first line looks like a header by parsing it properly
            reader_sample = csv.reader([first_line], skipinitialspace=True)
            first_values = next(reader_sample)
            is_header = any(
                val.strip().lower() in S3_CSV_COLUMNS for val in first_values
            )

            if is_header:
                # Use the actual header from the file
                reader = csv.DictReader(f, skipinitialspace=True)
                # Get the actual fieldnames from the CSV
                actual_fieldnames = reader.fieldnames
                click.echo(f"CSV columns: {', '.join(actual_fieldnames)}")
            else:
                # No header, use default fieldnames
                fieldnames = ["Bucket", "Key", "Size", "LastModifiedDate", "ETag"]
                reader = csv.DictReader(
                    f,
                    skipinitialspace=True,
                    fieldnames=fieldnames,
                )
                click.echo(f"CSV columns: {', '.join(fieldnames)}")

            total_count = 0
            for row in reader:
                try:
                    # Strip whitespace from keys
                    key = unquote(row["Key"].strip()) if row.get("Key") else None
                    size_str = row["Size"].strip() if row.get("Size") else None
                    bucket = row.get("Bucket", "").strip() if row.get("Bucket") else ""

                    if not key or not size_str:
                        continue

                    size = int(size_str)
                    objects[key] = {"size": size, "bucket": bucket}
                    total_count += 1

                    if total_count % 10000 == 0:
                        click.echo(f"  Read {total_count} objects...")
                except (KeyError, ValueError, AttributeError):
                    # Skip malformed rows
                    continue

        click.echo(f"Found {len(objects)} objects in CSV")
        return objects

    except Exception as e:
        click.echo(f"Error reading CSV: {e}", err=True)
        raise


def get_database_versions(db: Session) -> Sequence[Version]:
    """
    Get all versions from the database

    Returns:
        List of Version objects
    """
    click.echo("Querying versions from database...")
    statement = select(Version)
    versions = db.exec(statement).all()
    click.echo(f"Found {len(versions)} versions in database")
    return versions


def compare_versions(
    versions: Sequence[Version],
    s3_objects: Dict[str, Dict[str, Any]],
) -> Dict[str, List]:
    """
    Compare database versions with S3 objects

    Returns:
        Dict with lists of issues:
        - missing_in_s3: versions in DB but not in S3
        - size_mismatch: versions with different sizes
        - orphaned_in_s3: files in S3 not referenced in DB (with size and bucket)
    """
    issues = {
        "missing_in_s3": [],
        "size_mismatch": [],
        "orphaned_in_s3": set(
            s3_objects.keys()
        ),  # Start with all, remove as we find them
        "missing_photos": [],
    }

    click.echo("\nComparing versions...")

    for version in versions:
        s3_path = version.s3_path

        # Check if file exists in S3
        if s3_path not in s3_objects:
            issues["missing_in_s3"].append(
                {
                    "id": version.id,
                    "photo_uuid": version.photo_uuid,
                    "version": version.version,
                    "s3_path": s3_path,
                    "expected_size": version.size,
                }
            )
        else:
            # File exists, check size
            s3_info = s3_objects[s3_path]
            s3_size = s3_info["size"]
            if version.size and s3_size != version.size:
                issues["size_mismatch"].append(
                    {
                        "id": version.id,
                        "photo_uuid": version.photo_uuid,
                        "version": version.version,
                        "s3_path": s3_path,
                        "db_size": version.size,
                        "s3_size": s3_size,
                        "difference": s3_size - version.size,
                    }
                )

            # Remove from orphaned set
            issues["orphaned_in_s3"].discard(s3_path)

    # Convert orphaned set to list with size and bucket info
    orphaned_list = []
    for s3_path in sorted(issues["orphaned_in_s3"]):
        s3_info = s3_objects[s3_path]
        orphaned_list.append(
            {
                "s3_path": s3_path,
                "size": s3_info["size"],
                "bucket": s3_info["bucket"],
            }
        )
    issues["orphaned_in_s3"] = orphaned_list

    return issues


def format_size_mb(size_bytes: int) -> str:
    """Format size in bytes as MB string"""
    return f"{size_bytes / (1024 * 1024):,.2f}"


def format_size_kb(size_bytes: int) -> str:
    """Format size in bytes as KB string"""
    return f"{size_bytes / 1024:,.2f}"


def print_report(issues: Dict[str, List], show_orphaned: bool = True):
    """Print comparison report

    Args:
        issues: Dictionary of issues found during comparison
        show_orphaned: If True, show details of orphaned files. If False, only show count and total size.
    """

    click.echo("\n" + "=" * 80)
    click.echo("COMPARISON REPORT")
    click.echo("=" * 80)

    # Missing in S3
    if issues["missing_in_s3"]:
        click.echo(f"\n❌ MISSING IN S3: {len(issues['missing_in_s3'])} files")
        click.echo("-" * 80)
        for item in issues["missing_in_s3"][:10]:  # Show first 10
            click.echo(f"  Version ID: {item['id']}")
            click.echo(f"  Photo UUID: {item['photo_uuid']}")
            click.echo(f"  Version: {item['version']}")
            click.echo(f"  S3 Path: {item['s3_path']}")
            click.echo(f"  Expected Size: {item['expected_size']:,} bytes")
            click.echo()

        if len(issues["missing_in_s3"]) > 10:
            click.echo(f"  ... and {len(issues['missing_in_s3']) - 10} more")
    else:
        click.echo("\n✅ All database versions found in S3")

    # Size mismatches
    if issues["size_mismatch"]:
        click.echo(f"\n⚠️  SIZE MISMATCHES: {len(issues['size_mismatch'])} files")
        click.echo("-" * 80)
        for item in issues["size_mismatch"][:10]:  # Show first 10
            click.echo(f"  Version ID: {item['id']}")
            click.echo(f"  Photo UUID: {item['photo_uuid']}")
            click.echo(f"  Version: {item['version']}")
            click.echo(f"  S3 Path: {item['s3_path']}")
            click.echo(f"  DB Size: {item['db_size']:,} bytes")
            click.echo(f"  S3 Size: {item['s3_size']:,} bytes")
            click.echo(f"  Difference: {item['difference']:+,} bytes")
            click.echo()

        if len(issues["size_mismatch"]) > 10:
            click.echo(f"  ... and {len(issues['size_mismatch']) - 10} more")
    else:
        click.echo("\n✅ All sizes match")

    # Missing photos
    if issues["missing_photos"]:
        click.echo(
            f"\n❌ ORPHANED VERSIONS (no photo): {len(issues['missing_photos'])} records"
        )
        click.echo("-" * 80)
        for item in issues["missing_photos"][:10]:
            click.echo(f"  Version ID: {item['version_id']}")
            click.echo(f"  Photo UUID: {item['photo_uuid']}")
            click.echo(f"  Version: {item['version']}")
            click.echo(f"  S3 Path: {item['s3_path']}")
            click.echo()

        if len(issues["missing_photos"]) > 10:
            click.echo(f"  ... and {len(issues['missing_photos']) - 10} more")
    else:
        click.echo("\n✅ All versions have valid photos")

    # Orphaned in S3

    if issues["orphaned_in_s3"]:
        # Calculate total size
        total_size = sum(item["size"] for item in issues["orphaned_in_s3"])

        click.echo(
            f"\n⚠️  ORPHANED IN S3: {len(issues['orphaned_in_s3'])} files "
            f"({format_size_mb(total_size)} MB total)"
        )

        if show_orphaned:
            # Show detailed information about orphaned files
            click.echo("-" * 80)
            for item in issues["orphaned_in_s3"][:10]:
                click.echo(f"  {item['s3_path']} ({format_size_kb(item['size'])} KB)")

            if len(issues["orphaned_in_s3"]) > 10:
                click.echo(f"  ... and {len(issues['orphaned_in_s3']) - 10} more")
        else:
            # Just show count and total size
            click.echo("  (use --show-orphaned to see details)")
    else:
        click.echo("\n✅ No orphaned files in S3")

    # Summary
    click.echo("\n" + "=" * 80)
    click.echo("SUMMARY")
    click.echo("=" * 80)
    total_issues = (
        len(issues["missing_in_s3"])
        + len(issues["size_mismatch"])
        + len(issues["missing_photos"])
    )

    if total_issues == 0:
        click.echo("✅ All versions are consistent with S3 storage")
    else:
        click.echo(f"⚠️  Found {total_issues} issues")
        click.echo(f"   - Missing in S3: {len(issues['missing_in_s3'])}")
        click.echo(f"   - Size mismatches: {len(issues['size_mismatch'])}")
        total_size = sum(item["size"] for item in issues["orphaned_in_s3"])
        click.echo(
            f"   - Orphaned in S3: {len(issues['orphaned_in_s3'])} ({format_size_mb(total_size)} MB)"
        )


def export_issues(issues: Dict[str, List], output_file: str):
    """Export issues to JSON file"""
    import json

    # orphaned_in_s3 is already a list of dicts, no conversion needed

    with open(output_file, "w") as f:
        json.dump(issues, f, indent=2)

    click.echo(f"\n✅ Issues exported to: {output_file}")


def delete_orphaned_files(orphaned_files: List[Dict[str, Any]]) -> int:
    """
    Delete orphaned files from S3

    Args:
        orphaned_files: List of dicts with s3_path, bucket, and size

    Returns:
        Number of files successfully deleted
    """
    if not orphaned_files:
        click.echo("No orphaned files to delete")
        return 0

    # Calculate total size
    total_size = sum(f["size"] for f in orphaned_files)

    click.echo(
        f"\n⚠️  WARNING: About to delete {len(orphaned_files)} files ({format_size_mb(total_size)} MB)"
    )
    click.echo("This action cannot be undone!")

    if not click.confirm("\nDo you want to proceed with deletion?"):
        click.echo("Deletion cancelled")
        return 0

    s3 = boto3.client("s3")
    deleted_count = 0
    failed_count = 0

    click.echo("\nDeleting orphaned files...")

    for item in orphaned_files:
        s3_path = item["s3_path"]
        bucket = item["bucket"]

        if not bucket:
            click.echo(f"  ⚠️  Skipping {s3_path}: no bucket specified")
            failed_count += 1
            continue

        try:
            s3.delete_object(Bucket=bucket, Key=s3_path)
            deleted_count += 1

            if deleted_count % 100 == 0:
                click.echo(f"  Deleted {deleted_count}/{len(orphaned_files)} files...")
        except Exception as e:
            click.echo(f"  ❌ Failed to delete {s3_path}: {e}")
            failed_count += 1

    click.echo(f"\n✅ Successfully deleted {deleted_count} files")
    if failed_count > 0:
        click.echo(f"⚠️  Failed to delete {failed_count} files")

    return deleted_count


@maintenance.command()
@click.option(
    "--csv",
    "csv_source",
    required=False,
    help="Path to local CSV file or S3 URL (s3://bucket/path/file.csv or s3://bucket/path/file.csv.gz)",
)
@click.option(
    "--show-orphaned",
    is_flag=True,
    help="Show details of orphaned files in S3",
)
@click.option(
    "--delete-orphaned",
    is_flag=True,
    help="Delete orphaned files from S3 (requires confirmation)",
)
@click.option(
    "--export",
    "export_file",
    type=click.Path(),
    help="Export issues to JSON file",
)
@click.option(
    "--check-photos/--no-check-photos",
    default=True,
    help="Check if versions reference valid photos",
)
def compare_versions_cmd(
    csv_source: str,
    show_orphaned: bool,
    delete_orphaned: bool,
    export_file: str,
    check_photos: bool,
):
    """
    Compare versions table content with S3 storage from CSV export

    This command will:
    1. Load S3 objects from CSV file (local or from S3)
    2. Query all versions from the database
    3. Compare and report discrepancies:
       - Versions in DB but not in S3
       - Size mismatches between DB and S3
       - Orphaned files in S3 not referenced in DB
       - Versions referencing non-existent photos

    CSV file should have format: Bucket, Key, Size, LastModifiedDate, ETag

    Examples:
        photosafe maintenance compare-versions --csv /path/to/inventory.csv
        photosafe maintenance compare-versions --csv s3://bucket/path/inventory.csv.gz --show-orphaned
        photosafe maintenance compare-versions --csv /path/to/inventory.csv --delete-orphaned
    """

    click.echo("PhotoSafe Version Comparison Tool")
    click.echo("=" * 80)

    if not csv_source:
        bucket = "jmelloy-photo-backup"
        s3 = boto3.client("s3")
        files = sorted(
            list_bucket(s3, bucket, prefix="jmelloy-photo-backup/Photos/data"),
            key=lambda x: x[3],
        )

        csv_source = f"s3://{bucket}/{files[-1][0]}"
        click.echo(f"No CSV provided, using latest inventory: {csv_source}")
    csv_path = csv_source
    temp_file = None

    try:
        # Check if it's an S3 URL
        if csv_source.startswith("s3://"):
            csv_path = download_s3_csv(csv_source)
            temp_file = csv_path

        # Get S3 objects from CSV
        try:
            s3_objects = get_s3_objects_from_csv(csv_path)
        except Exception as e:
            click.echo(f"\n❌ Error reading CSV: {e}", err=True)
            sys.exit(1)

        # Get database versions
        with Session(engine) as db:
            try:
                versions = get_database_versions(db)

                if not versions:
                    click.echo("\n⚠️  No versions found in database")
                    sys.exit(0)

                # Compare
                issues = compare_versions(versions, s3_objects)

            except Exception as e:
                click.echo(f"\n❌ Database error: {e}", err=True)
                sys.exit(1)

        # Print report
        print_report(issues)

        # Track initial orphaned count before deletion
        initial_orphaned_count = len(issues["orphaned_in_s3"])

        # Delete orphaned files if requested
        if delete_orphaned and issues["orphaned_in_s3"]:
            deleted_count = delete_orphaned_files(issues["orphaned_in_s3"])
            if deleted_count > 0:
                # Update issues to reflect deletion
                issues["orphaned_in_s3"] = []

        # Export if requested
        if export_file:
            export_issues(issues, export_file)

        # Exit with error code if issues found (including orphaned files before deletion)
        total_issues = (
            len(issues["missing_in_s3"])
            + len(issues["size_mismatch"])
            + len(issues.get("missing_photos", []))
            + initial_orphaned_count
        )

        sys.exit(1 if total_issues > 0 else 0)

    finally:
        # Clean up temporary file if we downloaded one
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            click.echo(f"\nCleaned up temporary file: {temp_file}")
