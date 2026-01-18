#!/usr/bin/env python
"""PhotoSafe CLI - Sync commands for photo synchronization"""

import concurrent.futures
import json
import os
import shutil
from datetime import timezone

import boto3
import click
from dateutil import parser
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()


# Constants
MACOS_LIBRARY_NAME = "macOS Photos"


def clean_photo_data(photo_dict):
    """Clean up None values in photo data to prevent null insertions.

    This function modifies the input dictionary in place to clean up None values
    that could be serialized as JSON null in fields where they are not appropriate.

    Args:
        photo_dict: Dictionary of photo data from osxphotos

    Returns:
        The same dictionary with None values cleaned up (for chaining convenience)
    """
    # Filter None values from persons list
    persons = photo_dict.get("persons")
    if persons is None:
        photo_dict["persons"] = []
    elif isinstance(persons, list):
        # Remove None values from the persons list
        photo_dict["persons"] = [person for person in persons if person is not None]

    # Ensure place is an empty dict instead of None
    if photo_dict.get("place") is None:
        photo_dict["place"] = {}

    # Clean up face_info - filter out None values and empty/invalid entries
    face_info = photo_dict.get("face_info")
    if face_info is None:
        photo_dict["face_info"] = []
    elif isinstance(face_info, list):
        # Filter out None items from face_info list
        photo_dict["face_info"] = [face for face in face_info if face is not None]

    return photo_dict


@click.group()
def sync():
    """Sync photos from various sources"""
    pass


def get_filesize(path):
    try:
        return os.path.getsize(path)
    except Exception:
        return None


def get_photo_size(path):
    try:
        with Image.open(path) as img:
            return img.width, img.height
    except Exception:
        return None, None


@sync.command()
@click.option(
    "--bucket",
    default=lambda: os.environ.get("BUCKET", "jmelloy-photo-backup"),
    help="S3 bucket name",
)
@click.option(
    "--base-url",
    default=lambda: os.environ.get("BASE_URL", "http://localhost:8000"),
    help="PhotoSafe API base URL",
)
@click.option("--username", required=True, envvar="USERNAME", help="API username")
@click.option("--password", required=True, envvar="PASSWORD", help="API password")
@click.option(
    "--output-json",
    is_flag=True,
    help="Write JSON files for each photo (similar to iCloud dump)",
)
@click.option(
    "--skip-blocks-check",
    is_flag=True,
    help="Skip the blocks check and sync all photos",
)
def macos(bucket, base_url, username, password, output_json, skip_blocks_check):
    """Sync photos from macOS Photos library"""
    try:
        import osxphotos
    except ImportError:
        click.echo("Error: osxphotos is not installed. This command requires macOS.")
        click.echo("Install with: pip install osxphotos>=0.60")
        raise click.Abort()

    from cli.sync_tools import DateTimeEncoder, PhotoSafeAuth

    def get_versions(photo: osxphotos.PhotoInfo):
        vers = []
        dt = photo.date.astimezone(timezone.utc).strftime("%Y/%m/%d")
        uuid = photo._info["cloudAssetGUID"]

        base = os.path.join(username, dt, uuid)
        filename = photo.original_filename
        if photo.path:
            ext = os.path.splitext(photo.path)[1]
            path = os.path.join(base, "original", filename)
            size = get_filesize(photo.path)
            width, height = get_photo_size(photo.path)
            vers.append(
                {
                    "version": "original",
                    "s3_path": path,
                    "filename": filename,
                    "width": width,
                    "height": height,
                    "size": size,
                    "type": ext.lstrip(".").lower(),
                    "path": photo.path,
                }
            )
        if photo.path_live_photo:
            ext = os.path.splitext(photo.path_live_photo)[1]
            path = os.path.join(base, "live", os.path.splitext(filename)[0] + ext)
            size = get_filesize(photo.path_live_photo)
            width, height = get_photo_size(photo.path_live_photo)
            vers.append(
                {
                    "version": "live",
                    "s3_path": path,
                    "filename": os.path.splitext(filename)[0] + ext,
                    "width": width,
                    "height": height,
                    "size": size,
                    "type": ext.lstrip(".").lower(),
                    "path": photo.path_live_photo,
                }
            )

        d = {path: get_photo_size(path) for path in photo.path_derivatives or []}
        derivatives = sorted(
            d.items(), key=lambda x: x[1][0] * x[1][1] if x[1][0] and x[1][1] else 0
        )
        if derivatives:
            click.echo(f"Found {len(derivatives)} derivatives for photo {photo.uuid}")
            thumbnail = derivatives[0][0]
            ext = os.path.splitext(thumbnail)[1]
            path = os.path.join(base, "thumbnail", os.path.splitext(filename)[0] + ext)
            width, height = derivatives[0][1]

            vers.append(
                {
                    "version": "thumb",
                    "s3_path": path,
                    "filename": os.path.splitext(filename)[0] + ext,
                    "width": width,
                    "height": height,
                    "size": get_filesize(thumbnail),
                    "type": ext.lstrip(".").lower(),
                    "path": thumbnail,
                }
            )

            medium = derivatives[-1][0]
            if medium != thumbnail:
                ext = os.path.splitext(medium)[1]
                path = os.path.join(base, "medium", os.path.splitext(filename)[0] + ext)
                width, height = derivatives[-1][1]
                vers.append(
                    {
                        "version": "medium",
                        "s3_path": path,
                        "filename": os.path.splitext(filename)[0] + ext,
                        "width": width,
                        "height": height,
                        "size": get_filesize(medium),
                        "type": ext.lstrip(".").lower(),
                        "path": medium,
                    }
                )
        return vers

    photos_db = osxphotos.PhotosDB()
    base_path = photos_db.library_path
    if not base_path:
        click.echo("Error: Could not determine Photos library path", err=True)
        raise click.Abort()

    # Initialize S3 client
    s3 = boto3.client("s3", "us-west-2")

    # Authenticate
    auth = PhotoSafeAuth(base_url, username, password)

    # Populate blocks
    total = 0
    blocks = {}
    for photo in photos_db.photos():
        dt = photo.date.astimezone(timezone.utc)
        if not photo._info["cloudAssetGUID"]:
            continue

        total = total + 1

        if dt.year not in blocks:
            blocks[dt.year] = {}

        if dt.month not in blocks[dt.year]:
            blocks[dt.year][dt.month] = {}

        if dt.day not in blocks[dt.year][dt.month]:
            blocks[dt.year][dt.month][dt.day] = []

        blocks[dt.year][dt.month][dt.day].append(photo)

    # Find discrepancies
    photos_to_process = []

    if skip_blocks_check:
        # Skip blocks check and process all photos
        click.echo("Skipping blocks check, processing all photos")
        for year, months in sorted(blocks.items()):
            for month, days in sorted(months.items()):
                for day, photos in sorted(days.items()):
                    photos_to_process.extend(photos)
    else:
        # Get server blocks
        r = auth.get("/api/photos/blocks")
        r.raise_for_status()
        server_blocks = r.json()

        for year, months in sorted(blocks.items()):
            for month, days in sorted(months.items()):
                for day, photos in sorted(days.items()):
                    count = len(photos)
                    date = max([x.date_modified or x.date for x in photos])
                    vals = (
                        server_blocks.get(str(year), {})
                        .get(str(month), {})
                        .get(str(day), {})
                    )
                    # Check for count discrepancy or date discrepancy
                    has_discrepancy = False
                    if vals:
                        if vals["count"] != count:
                            has_discrepancy = True
                        # Also check if the max date on server is older than local
                        elif "max_date" in vals and vals["max_date"]:
                            server_date = parser.parse(vals["max_date"])
                            # Make both dates timezone-aware for proper comparison
                            if date.tzinfo is None:
                                date = date.replace(tzinfo=timezone.utc)
                            if server_date.tzinfo is None:
                                server_date = server_date.replace(tzinfo=timezone.utc)
                            if server_date < date:
                                has_discrepancy = True

                    if has_discrepancy:
                        click.echo(
                            f"Discrepancy {year}/{month}/{day}, {vals} vs {count}/{date}"
                        )
                        photos_to_process.extend(blocks[year][month][day])

    click.echo(f"Total: {total}, to process: {len(photos_to_process)}")

    # Sync photos
    def sync_photo(photo: osxphotos.PhotoInfo):
        p = photo.asdict()
        p["masterFingerprint"] = photo._info["masterFingerprint"]
        if not photo._info["cloudAssetGUID"]:
            return

        p["uuid"] = photo._info["cloudAssetGUID"]
        for k, v in p.items():
            if base_path and v and type(v) is str and base_path in v:
                p[k] = v.replace(base_path, "")

        # Clean up None values to prevent null insertions
        p = clean_photo_data(p)

        # If photo is in trash and all files are gone, soft delete it
        if photo.intrash:
            try:
                r = auth.delete(f"/api/photos/{p['uuid']}/")
                click.echo(f"Photo {p['uuid'].lower()} is in trash, deleting...")
                if r.status_code == 404:
                    click.echo(f"Photo {p['uuid'].lower()} already deleted on server")
                elif r.status_code == 200:
                    click.echo(
                        f"Deleted photo {p['uuid'].lower()} {photo.original_filename}"
                    )
                else:
                    r.raise_for_status()
                return
            except Exception as e:
                click.echo(f"Error deleting photo {photo.uuid}: {str(e)}", err=True)
                return

        if photo.search_info:
            p["search_info"] = photo.search_info.asdict()

        # Write JSON file if requested
        if output_json:
            dt = photo.date.astimezone(timezone.utc)
            directory = os.path.join(MACOS_LIBRARY_NAME, dt.strftime("%Y/%m/%d"))
            os.makedirs(directory, exist_ok=True)
            json_path = os.path.join(directory, f"{p['uuid']}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(p, cls=DateTimeEncoder, indent=2))

        try:
            r = auth.patch(
                f"/api/photos/{p['uuid']}/",
                data=json.dumps(p, cls=DateTimeEncoder),
                headers={"Content-Type": "application/json"},
            )

            if r.status_code == 404:
                # Check if photo is not in trash
                if photo.path and "/originals/" in photo.path.lower():
                    click.echo(
                        f"Creating photo {p['uuid'].lower()} {photo.original_filename} with versions"
                    )

                    # Build versions list
                    versions = get_versions(photo)
                    for v in versions:
                        # Remove local path from version info before sending to server
                        if "path" in v:
                            s3.upload_file(v["path"], bucket, v["s3_path"])
                            del v["path"]

                    # Add versions to photo data
                    p["versions"] = versions

                    # Try to create the photo
                    try:
                        r = auth.post(
                            "/api/photos/",
                            data=json.dumps(p, cls=DateTimeEncoder),
                            headers={"Content-Type": "application/json"},
                        )
                        r.raise_for_status()
                        click.echo(
                            f"Created photo {p['uuid'].lower()} {photo.original_filename} ({r.status_code})"
                        )
                    except Exception as create_error:
                        click.echo(
                            f"Error creating photo {photo.uuid}: {str(create_error)}",
                            err=True,
                        )
                else:
                    click.echo(
                        f"Skipping missing photo {p['uuid'].lower()} {photo.original_filename} (in trash or no original path)"
                    )
                return
            r.raise_for_status()
            click.echo(
                f"Synced {p['uuid'].lower()} {photo.original_filename} ({r.status_code})..."
            )
        except Exception as e:
            click.echo(f"Error syncing photo {photo.uuid}: {str(e)}", err=True)
            return

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(sync_photo, photos_to_process)
        results = list(futures)
        click.echo(
            f"{len(results)} checked, {len(list(filter(None, results)))} uploaded"
        )


@sync.command()
@click.option("--limit", help="Number of photos to export", type=int)
def dump_macos(limit):
    """Dump sample photos from macOS Photos library to JSON fixtures"""
    try:
        import osxphotos
    except ImportError:
        click.echo("Error: osxphotos is not installed. This command requires macOS.")
        click.echo("Install with: pip install osxphotos>=0.60")
        raise click.Abort()

    from .sync_tools import DateTimeEncoder

    photos_db = osxphotos.PhotosDB()
    base_path = photos_db.library_path

    sample_photos = []

    for i, photo in enumerate(photos_db.photos()):
        if limit and i >= limit:
            break

        if (i + 1) % 1000 == 0:
            click.echo(f"Processing photo {i + 1}: {photo.filename}")

        p = photo.asdict()
        p["masterFingerprint"] = photo._info["masterFingerprint"]
        if not photo._info["cloudAssetGUID"]:
            continue

        p["uuid"] = photo._info["cloudAssetGUID"]
        for k, v in p.items():
            if v and type(v) is str and base_path in v:
                p[k] = v.replace(base_path, "")

        # Clean up None values to prevent null insertions
        p = clean_photo_data(p)

        directory = os.path.join(
            p["library"] or "PrimarySync", photo.date.strftime("%Y/%m/%d")
        )
        os.makedirs(directory, exist_ok=True)
        with open(
            os.path.join(directory, f"{photo._info['cloudAssetGUID']}.json"),
            "wb",
        ) as FILE:
            FILE.write(json.dumps(p, cls=DateTimeEncoder, indent=2).encode("utf-8"))

        if limit:
            sample_photos.append(p)

    if limit:
        os.makedirs("fixtures", exist_ok=True)
        with open("fixtures/macos_sample.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_photos, cls=DateTimeEncoder, indent=2))

        click.echo(
            f"Exported {len(sample_photos)} photos to fixtures/macos_sample.json"
        )


@sync.command()
@click.option(
    "--bucket",
    default=lambda: os.environ.get("BUCKET", "jmelloy-photo-backup"),
    help="S3 bucket name",
)
@click.option(
    "--base-url",
    default=lambda: os.environ.get("BASE_URL", "http://localhost:8000"),
    help="PhotoSafe API base URL",
)
@click.option("--username", required=True, envvar="USERNAME", help="API username")
@click.option("--password", required=True, envvar="PASSWORD", help="API password")
@click.option("--icloud-username", envvar="ICLOUD_USERNAME", help="iCloud username")
@click.option("--icloud-password", envvar="ICLOUD_PASSWORD", help="iCloud password")
@click.option(
    "--use-stored-credentials",
    is_flag=True,
    help="Use stored Apple credentials from database (requires prior authentication via web interface)",
)
@click.option(
    "--credential-id",
    type=int,
    help="Specific credential ID to use from database (optional, requires --use-stored-credentials)",
)
@click.option("--stop-after", default=1000, help="Stop after N existing photos")
@click.option("--offset", default=0, help="Offset for fetching photos")
@click.option(
    "--batch-size", default=10, help="Number of photos to process in each batch"
)
@click.option("--library", help="Filter by library name (optional)")
def icloud(
    bucket,
    base_url,
    username,
    password,
    icloud_username,
    icloud_password,
    use_stored_credentials,
    credential_id,
    stop_after,
    offset,
    batch_size,
    library,
):
    """Sync photos from iCloud"""
    import mimetypes

    import boto3
    from tqdm import tqdm

    from .sync_tools import (
        DateTimeEncoder,
        PhotoSafeAuth,
        authenticate_icloud,
        get_icloud_from_stored_credentials,
        list_bucket,
    )

    s3 = boto3.client("s3", "us-west-2")

    # Authenticate with API
    auth = PhotoSafeAuth(base_url, username, password)

    # Authenticate with iCloud
    if use_stored_credentials:
        # Use stored credentials from database
        if credential_id:
            api = get_icloud_from_stored_credentials(credential_id=credential_id)
        else:
            # Use credentials for the authenticated user
            api = get_icloud_from_stored_credentials(user_id=auth.user["id"])

        if not api:
            click.echo(
                "Failed to authenticate with stored credentials. "
                "Please ensure you have authenticated via the web interface at /settings/apple",
                err=True
            )
            raise click.Abort()
    else:
        # Use traditional username/password authentication
        api = authenticate_icloud(icloud_username, icloud_password)

    def upload_photo(photo, version, path):
        os.makedirs(os.path.split(path)[0], exist_ok=True)
        r = photo.download(version)
        r.raise_for_status()
        size = photo.versions[version]["size"]

        with open(path, "wb") as FILE:
            shutil.copyfileobj(r.raw, FILE)

        suffix = os.path.splitext(path)[-1].lower()
        content_type = mimetypes.types_map.get(suffix)
        if suffix == ".heic":
            content_type = "image/heic"
        if not content_type:
            content_type = "application/octet-stream"

        with tqdm(
            total=size,
            desc=f"{path}",
            bar_format="{percentage:.1f}%|{bar:25} | {rate_fmt} | {desc}",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            s3.upload_file(
                path,
                bucket,
                path,
                ExtraArgs=dict(ContentType=content_type),
                Callback=pbar.update,
            )
        os.remove(path)

    _albums = {}

    def album_contains(album_name, photo):
        if album_name in _albums:
            return photo.id in _albums[album_name]
        photos = []
        click.echo(f"Loading album {album_name}")
        for p in api.photos.albums.get(album_name, []):
            photos.append(p.id)
        _albums[album_name] = photos
        return photo.id in photos

    def upload_albums():
        for name, album in api.photos.albums.items():
            print(f"Processing album {name}")
            if album.name == "All Photos" or not album.id:
                continue

            album_info = {
                "uuid": album.id,
                "title": album.title,
                "creation_date": album.created,
            }
            album_info["photos"] = list(
                map(
                    lambda photo: photo._asset_record["recordName"],
                    album.photos,
                )
            )

            if not album_info["photos"]:
                continue

            r = auth.put(
                f"/api/albums/{album.id}/",
                data=json.dumps(album_info, cls=DateTimeEncoder),
                headers={"Content-Type": "application/json"},
            )

            if r.status_code == 404:
                r = auth.post(
                    "/api/albums/",
                    data=json.dumps(album_info, cls=DateTimeEncoder),
                    headers={"Content-Type": "application/json"},
                )

            if r.status_code >= 400:
                print(r.json(), album_info)

    s3_keys = {}
    os.makedirs(username, exist_ok=True)

    # Track totals across all libraries
    total_photos = 0
    total_created_all = 0
    total_updated_all = 0

    # Filter libraries if specified
    libraries_to_process = {}
    if library:
        # Check if the specified library exists
        if library not in api.photos.libraries:
            available_libraries = ", ".join(api.photos.libraries.keys())
            click.echo(
                f"Error: Library '{library}' not found. Available libraries: {available_libraries}",
                err=True,
            )
            raise click.Abort()
        libraries_to_process[library] = api.photos.libraries[library]
        click.echo(f"Filtering to library: {library}")
    else:
        libraries_to_process = api.photos.libraries

    for library_name, library_obj in libraries_to_process.items():
        click.echo(f"Library: {library_name}")
        photo_batch = []  # Collect photos for batching
        total_created = 0
        total_updated = 0
        photo_count = 0  # Track total photos processed in this library

        def send_batch():
            """Send accumulated batch of photos to the API"""
            nonlocal total_created, total_updated

            if not photo_batch:
                return

            batch_data = {"photos": photo_batch}

            r = auth.post(
                "/api/photos/batch/",
                data=json.dumps(batch_data, cls=DateTimeEncoder).replace("\\u0000", ""),
                headers={"Content-Type": "application/json"},
            )

            if r.status_code == 200:
                result = r.json()
                total_created += result["created"]
                total_updated += result["updated"]
                click.echo(
                    f"Batch processed: {result['created']} created, total: {total_created} created, "
                    f"{result['updated']} updated, total: {total_updated} updated, {result['errors']} errors"
                )

                # Log any errors
                for photo_result in result["results"]:
                    if not photo_result["success"]:
                        click.echo(
                            f"Error processing {photo_result['uuid']}: {photo_result.get('error', 'Unknown error')}",
                            err=True,
                        )
            else:
                click.echo(f"Batch request failed: {r.status_code} {r.text}", err=True)
                r.raise_for_status()

            photo_batch.clear()

        for i, photo in enumerate(library_obj.all.fetch_records(offset)):
            photo_count = i + 1  # Track photo count
            # click.echo(f"{photo}, {photo.created}")
            dt = (photo.asset_date or photo.created).strftime("%Y/%m/%d")

            objects = s3_keys.get(dt)
            if not objects:
                objects = {
                    x[0]: x[1]
                    for x in list_bucket(
                        s3,
                        bucket=bucket,
                        prefix=os.path.join(os.path.join(username, dt)),
                    )
                }
                s3_keys[dt] = objects
                for key in list(s3_keys):
                    if key[0:7] > dt[0:7]:
                        del s3_keys[key]

            exif = None
            metadata = photo.mediaMetaData
            if metadata:
                exif = metadata.get("{Exif}")

            lat, long = None, None
            try:
                lat = photo.latitude
            except Exception:
                print(f"{photo=} has no latitude")
            try:
                long = photo.longitude
            except Exception:
                print(f"{photo=} has no longitude")

            data = {
                "uuid": photo._asset_record["recordName"],
                "masterFingerprint": photo.id,
                "original_filename": photo.filename,
                "date": photo.asset_date or photo.created,
                "versions": [],
                "size": photo.size,
                "uti": photo.versions["original"]["type"],
                "width": photo.dimensions[0],
                "height": photo.dimensions[1],
                "hidden": photo.isHidden,
                "favorite": photo.isFavorite,
                "title": photo.caption,
                "description": photo.description,
                "latitude": lat,
                "longitude": long,
                "exif": exif,
                "live_photo": "live" in photo.versions,
                "isphoto": photo.item_type == "image",
                "ismovie": photo.item_type == "movie",
                "screenshot": album_contains("Screenshots", photo),
                "slow_mo": album_contains("Slo-mo", photo),
                "time_lapse": album_contains("Time-lapse", photo),
                "panorama": album_contains("Panoramas", photo),
                "burst": album_contains("Bursts", photo),
                "portrait": album_contains("Portrait", photo),
                "library": library_name,
                "fields": photo.fields,
            }

            keys = {
                "medium": "s3_key_path",
                "thumb": "s3_thumbnail_path",
                "original": "s3_original_path",
                "live": "s3_live_path",
            }

            for version, details in photo.versions.items():
                path = os.path.join(
                    username, dt, data["uuid"], version, details["filename"]
                )
                if path not in objects or objects[path] != details["size"]:
                    upload_photo(photo, version, path)
                if version in keys:
                    data[keys[version]] = path

                data["versions"].append(
                    dict(
                        version=version,
                        s3_path=path,
                        filename=details["filename"],
                        width=details["width"],
                        height=details["height"],
                        size=details["size"],
                        type=path.split(".")[-1].lower(),
                    )
                )

            # Add photo to batch
            photo_batch.append(data)

            # Send batch when it reaches the batch size
            if len(photo_batch) >= batch_size:
                send_batch()

                # Check stop condition after sending batch
                if total_updated > stop_after:
                    break

        # Send any remaining photos in the final batch
        send_batch()

        # Accumulate totals from this library
        total_photos += photo_count
        total_created_all += total_created
        total_updated_all += total_updated

    # Process shared albums
    if hasattr(api.photos, 'shared_albums') and api.photos.shared_albums:
        click.echo("Processing shared albums")
        for album_name, shared_album in api.photos.shared_albums.items():
            click.echo(f"Shared Album: Shared: {album_name}")
            photo_batch = []
            total_created = 0
            total_updated = 0
            photo_count = 0

            def send_batch():
                """Send accumulated batch of photos to the API"""
                nonlocal total_created, total_updated

                if not photo_batch:
                    return

                batch_data = {"photos": photo_batch}

                r = auth.post(
                    "/api/photos/batch/",
                    data=json.dumps(batch_data, cls=DateTimeEncoder).replace("\\u0000", ""),
                    headers={"Content-Type": "application/json"},
                )

                if r.status_code == 200:
                    result = r.json()
                    total_created += result["created"]
                    total_updated += result["updated"]
                    click.echo(
                        f"Batch processed: {result['created']} created, total: {total_created} created, "
                        f"{result['updated']} updated, total: {total_updated} updated, {result['errors']} errors"
                    )

                    # Log any errors
                    for photo_result in result["results"]:
                        if not photo_result["success"]:
                            click.echo(
                                f"Error processing {photo_result['uuid']}: {photo_result.get('error', 'Unknown error')}",
                                err=True,
                            )
                else:
                    click.echo(f"Batch request failed: {r.status_code} {r.text}", err=True)
                    r.raise_for_status()

                photo_batch.clear()

            for i, photo in enumerate(shared_album.photos):
                photo_count = i + 1
                dt = (photo.asset_date or photo.created).strftime("%Y/%m/%d")

                objects = s3_keys.get(dt)
                if not objects:
                    objects = {
                        x[0]: x[1]
                        for x in list_bucket(
                            s3,
                            bucket=bucket,
                            prefix=os.path.join(os.path.join(username, dt)),
                        )
                    }
                    s3_keys[dt] = objects
                    for key in list(s3_keys):
                        if key[0:7] > dt[0:7]:
                            del s3_keys[key]

                exif = None
                metadata = photo.mediaMetaData
                if metadata:
                    exif = metadata.get("{Exif}")

                lat, long = None, None
                try:
                    lat = photo.latitude
                except Exception:
                    print(f"{photo=} has no latitude")
                try:
                    long = photo.longitude
                except Exception:
                    print(f"{photo=} has no longitude")

                data = {
                    "uuid": photo._asset_record["recordName"],
                    "masterFingerprint": photo.id,
                    "original_filename": photo.filename,
                    "date": photo.asset_date or photo.created,
                    "versions": [],
                    "size": photo.size,
                    "uti": photo.versions["original"]["type"],
                    "width": photo.dimensions[0],
                    "height": photo.dimensions[1],
                    "hidden": photo.isHidden,
                    "favorite": photo.isFavorite,
                    "title": photo.caption,
                    "description": photo.description,
                    "latitude": lat,
                    "longitude": long,
                    "exif": exif,
                    "live_photo": "live" in photo.versions,
                    "isphoto": photo.item_type == "image",
                    "ismovie": photo.item_type == "movie",
                    "screenshot": album_contains("Screenshots", photo),
                    "slow_mo": album_contains("Slo-mo", photo),
                    "time_lapse": album_contains("Time-lapse", photo),
                    "panorama": album_contains("Panoramas", photo),
                    "burst": album_contains("Bursts", photo),
                    "portrait": album_contains("Portrait", photo),
                    "library": f"Shared: {album_name}",
                    "fields": photo.fields,
                }

                keys = {
                    "medium": "s3_key_path",
                    "thumb": "s3_thumbnail_path",
                    "original": "s3_original_path",
                    "live": "s3_live_path",
                }

                for version, details in photo.versions.items():
                    path = os.path.join(
                        username, dt, data["uuid"], version, details["filename"]
                    )
                    if path not in objects or objects[path] != details["size"]:
                        upload_photo(photo, version, path)
                    if version in keys:
                        data[keys[version]] = path

                    data["versions"].append(
                        dict(
                            version=version,
                            s3_path=path,
                            filename=details["filename"],
                            width=details["width"],
                            height=details["height"],
                            size=details["size"],
                            type=path.split(".")[-1].lower(),
                        )
                    )

                # Add photo to batch
                photo_batch.append(data)

                # Send batch when it reaches the batch size
                if len(photo_batch) >= batch_size:
                    send_batch()

                    # Check stop condition after sending batch
                    if total_updated > stop_after:
                        break

            # Send any remaining photos in the final batch
            send_batch()

            # Accumulate totals from this shared album
            total_photos += photo_count
            total_created_all += total_created
            total_updated_all += total_updated

    shutil.rmtree(username)
    click.echo(
        f"{total_photos} photos processed, {total_created_all} created, {total_updated_all} updated"
    )
    upload_albums()


@sync.command()
@click.option("--icloud-username", envvar="ICLOUD_USERNAME", help="iCloud username")
@click.option("--icloud-password", envvar="ICLOUD_PASSWORD", help="iCloud password")
def list_libraries(icloud_username, icloud_password):
    """List available iCloud photo libraries"""
    from .sync_tools import authenticate_icloud

    # Authenticate with iCloud
    api = authenticate_icloud(icloud_username, icloud_password)

    click.echo("\nAvailable iCloud Photo Libraries:")
    click.echo("-" * 50)

    if not api.photos.libraries:
        click.echo("No libraries found")
        return

    for library_name, library in api.photos.libraries.items():
        click.echo(f"  • {library_name}")

    click.echo()


@sync.command()
@click.option("--icloud-username", envvar="ICLOUD_USERNAME", help="iCloud username")
@click.option("--icloud-password", envvar="ICLOUD_PASSWORD", help="iCloud password")
@click.option(
    "--output", default="fixtures/icloud_sample.json", help="Output JSON file path"
)
@click.option("--limit", default=25, help="Number of photos to export")
def dump_icloud(icloud_username, icloud_password, output, limit):
    """Dump sample photos from iCloud to a JSON fixtures file"""

    from .sync_tools import DateTimeEncoder, authenticate_icloud

    # Authenticate with iCloud
    api = authenticate_icloud(icloud_username, icloud_password)

    sample_photos = []

    # Iterate through libraries and collect sample photos
    for library_name, library in api.photos.libraries.items():
        click.echo(f"Processing library: {library_name}")

        for i, photo in enumerate(library.all.fetch_records(0)):
            if len(sample_photos) >= limit:
                break

            click.echo(f"Processing photo {i + 1}: {photo.filename}")

            date = photo.asset_date or photo.created
            data = {
                k: v
                for k, v in photo.__dict__.items()
                if k == "_asset_record" or not k.startswith("_")
            }
            data["versions"] = photo.versions

            directory = os.path.join(library_name, date.strftime("%Y/%m/%d"))
            os.makedirs(directory, exist_ok=True)
            with open(
                os.path.join(directory, f"{photo._asset_record['recordName']}.json"),
                "wb",
            ) as FILE:
                FILE.write(
                    json.dumps(data, cls=DateTimeEncoder, indent=2).encode("utf-8")
                )

            if limit:
                sample_photos.append(data)

    if limit:
        os.makedirs("fixtures", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_photos, cls=DateTimeEncoder, indent=2))

    click.echo(f"Exported {len(sample_photos)} photos to {output}")
