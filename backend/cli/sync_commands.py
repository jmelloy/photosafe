#!/usr/bin/env python
"""PhotoSafe CLI - Sync commands for photo synchronization"""

import concurrent.futures
import json
import os
from datetime import datetime, timedelta, timezone

import boto3
import click
import requests
from dateutil import parser


@click.group()
def sync():
    """Sync photos from various sources"""
    pass


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
def macos(bucket, base_url, username, password):
    """Sync photos from macOS Photos library"""
    try:
        import osxphotos
    except ImportError:
        click.echo("Error: osxphotos is not installed. This command requires macOS.")
        click.echo("Install with: pip install osxphotos>=0.60")
        raise click.Abort()

    from .sync_tools import DateTimeEncoder

    photos_db = osxphotos.PhotosDB()
    base_path = photos_db.library_path
    s3 = boto3.client("s3", "us-west-2")

    # Authenticate
    r = requests.post(
        f"{base_url}/api/auth/login", data={"username": username, "password": password}
    )
    r.raise_for_status()
    token = r.json()["access_token"]

    r = requests.get(
        f"{base_url}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    user = r.json()

    click.echo(f"Authenticated as {user.get('username')}")

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

    # Get server blocks
    r = requests.get(
        f"{base_url}/photos/blocks", headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    server_blocks = r.json()

    # Find discrepancies
    photos_to_process = []
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
                if vals and (
                    vals["count"] != count
                    or abs(parser.parse(vals["max_date"]) - date) > timedelta(seconds=3)
                ):
                    click.echo(
                        f"Discrepancy {year}/{month}/{day}, {vals} vs {count}/{date}"
                    )
                    photos_to_process.extend(blocks[year][month][day])

    click.echo(f"Total: {total}, to process: {len(photos_to_process)}")

    # Sync photos
    def sync_photo(photo):
        p = photo.asdict()
        p["masterFingerprint"] = photo._info["masterFingerprint"]
        if not photo._info["cloudAssetGUID"]:
            return

        p["uuid"] = photo._info["cloudAssetGUID"]
        for k, v in p.items():
            if v and type(v) is str and base_path in v:
                p[k] = v.replace(base_path, "")

        r = requests.patch(
            f"{base_url}/api/photos/{p['uuid']}/",
            data=json.dumps(p, cls=DateTimeEncoder),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

        if r.status_code == 404:
            return
        r.raise_for_status()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(sync_photo, photos_to_process)
        results = list(futures)
        click.echo(
            f"{len(results)} checked, {len(list(filter(None, results)))} uploaded"
        )


@sync.command()
@click.option(
    "--bucket",
    default=lambda: os.environ.get("BUCKET", "jmelloy-photo-backup"),
    help="S3 bucket name",
)
@click.option(
    "--base-url",
    default=lambda: os.environ.get("BASE_URL", "https://api.photosafe.melloy.life"),
    help="PhotoSafe API base URL",
)
@click.option("--username", required=True, envvar="USERNAME", help="API username")
@click.option("--password", required=True, envvar="PASSWORD", help="API password")
@click.option("--icloud-username", envvar="ICLOUD_USERNAME", help="iCloud username")
@click.option("--icloud-password", envvar="ICLOUD_PASSWORD", help="iCloud password")
@click.option("--stop-after", default=1000, help="Stop after N existing photos")
@click.option("--offset", default=0, help="Offset for fetching photos")
def icloud(
    bucket,
    base_url,
    username,
    password,
    icloud_username,
    icloud_password,
    stop_after,
    offset,
):
    """Sync photos from iCloud"""
    import mimetypes
    import shutil
    import sys

    import boto3
    from pyicloud import PyiCloudService
    from tqdm import tqdm

    from .sync_tools import DateTimeEncoder, list_bucket

    s3 = boto3.client("s3", "us-west-2")

    # Authenticate with API
    r = requests.post(
        f"{base_url}/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    r.raise_for_status()
    token = r.json()["access_token"]

    r = requests.get(
        f"{base_url}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    user = r.json()

    click.echo(f"Authenticated as {user.get('username')}")

    # Authenticate with iCloud
    if not icloud_username:
        icloud_username = click.prompt("iCloud Username")
    if not icloud_password:
        icloud_password = click.prompt("iCloud Password", hide_input=True)

    api = PyiCloudService(icloud_username, icloud_password)

    if api.requires_2fa:
        click.echo("Two-factor authentication required.")
        code = click.prompt(
            "Enter the code you received on one of your approved devices"
        )
        result = api.validate_2fa_code(code)
        click.echo(f"Code validation result: {result}")

        if not result:
            click.echo("Failed to verify security code")
            raise click.Abort()

        if not api.is_trusted_session:
            click.echo("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            click.echo(f"Session trust result: {result}")

            if not result:
                click.echo(
                    "Failed to request trust. You will likely be prompted for the code again in the coming weeks"
                )
    elif api.requires_2sa:
        click.echo("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            click.echo(
                f"  {i}: {device.get('deviceName', 'SMS to %s' % device.get('phoneNumber'))}"
            )

        device_idx = click.prompt(
            "Which device would you like to use?", type=int, default=0
        )
        device = devices[device_idx]
        if not api.send_verification_code(device):
            click.echo("Failed to send verification code")
            raise click.Abort()

        code = click.prompt("Please enter validation code")
        if not api.validate_verification_code(device, code):
            click.echo("Failed to verify verification code")
            raise click.Abort()

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

    s3_keys = {}
    os.makedirs(username, exist_ok=True)

    for library_name, library in api.photos.libraries.items():
        click.echo(f"Library: {library_name}")
        existing = 0

        for i, photo in enumerate(library.all.fetch_records(offset)):
            click.echo(f"{photo}, {photo.created}")
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

            r = requests.post(
                f"{base_url}/api/photos/",
                data=json.dumps(data, cls=DateTimeEncoder).replace("\\u0000", ""),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
            )

            if r.status_code == 400 and "this uuid already exists" in r.text:
                existing += 1

                if existing > stop_after:
                    break

                r = requests.patch(
                    f"{base_url}/api/photos/{data['uuid']}/",
                    data=json.dumps(data, cls=DateTimeEncoder).replace("\\u0000", ""),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                    },
                )

            elif r.status_code > 399:
                click.echo(f"{r.status_code} {r.text}")
                r.raise_for_status()

    shutil.rmtree(username)
    click.echo(f"{i + 1} photos, {existing} existing")


@sync.command()
@click.option(
    "--bucket",
    default=lambda: os.environ.get("BUCKET", "jmelloy-photo-backup"),
    help="S3 bucket name",
)
@click.option(
    "--base-url",
    default=lambda: os.environ.get("BASE_URL", "https://api.photosafe.melloy.life"),
    help="PhotoSafe API base URL",
)
@click.option("--username", required=True, envvar="USERNAME", help="API username")
@click.option("--password", required=True, envvar="PASSWORD", help="API password")
@click.option(
    "--leonardo-key", required=True, envvar="LEONARDO_KEY", help="Leonardo AI API key"
)
@click.option("--stop-after", default=5, help="Stop after N existing photos")
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="Set the log level",
)
def leonardo(bucket, base_url, username, password, leonardo_key, stop_after, log_level):
    """Sync AI-generated images from Leonardo.ai"""
    import datetime
    import io
    import logging
    from copy import copy
    from urllib.parse import urlparse

    import boto3
    import requests
    from PIL import Image

    from .sync_tools import DateTimeEncoder, list_bucket

    logging.basicConfig(
        format="%(asctime)s %(levelname)6s %(message)s",
        datefmt="%b %d %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    s3 = boto3.client("s3", "us-west-2")

    # Authenticate with API
    r = requests.post(
        f"{base_url}/api/auth/login", data={"username": username, "password": password}
    )
    r.raise_for_status()
    token = r.json()["access_token"]

    r = requests.get(
        f"{base_url}/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    user = r.json()

    click.echo(f"Authenticated as {user.get('username')}")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    session.headers.update({"Content-Type": "application/json"})

    leonardo_session = requests.Session()
    leonardo_session.headers.update({"Authorization": f"Bearer {leonardo_key}"})
    leonardo_session.headers.update({"Accept": "application/json"})

    def wrap(session, url, data={}, method="POST"):
        logger.info(f"Calling {method} {url}")
        start = datetime.datetime.now()

        if method.upper() == "GET":
            resp = session.get(f"{url}", params=data)
        elif method.upper() == "POST":
            resp = session.post(
                f"{url}",
                data=json.dumps(data, cls=DateTimeEncoder),
            )
        elif method.upper() == "PUT":
            resp = session.put(
                f"{url}",
                data=json.dumps(data, cls=DateTimeEncoder),
            )
        elif method.upper() == "DELETE":
            resp = session.delete(f"{url}")
        elif method.upper() == "PATCH":
            resp = session.patch(
                f"{url}",
                data=json.dumps(data, cls=DateTimeEncoder),
            )

        end = datetime.datetime.now()
        logger.info(f" --> {resp.status_code} - {end - start}")
        logger.debug(f"{json.dumps(resp.json(), indent=2)}")

        if resp.status_code > 205:
            logger.warning(resp.text)

        return resp.json(), resp

    def get_model(id: str) -> dict:
        url = f"https://cloud.leonardo.ai/api/rest/v1/models/{id}"
        data, r = wrap(leonardo_session, url, {}, "GET")
        r.raise_for_status()
        return data

    def generations(
        offset, limit, user_id="278a9059-6820-4882-aec1-a02d0c7867af"
    ) -> dict:
        url = f"https://cloud.leonardo.ai/api/rest/v1/generations/user/{user_id}"
        data, r = wrap(leonardo_session, url, {"offset": offset, "limit": limit}, "GET")
        r.raise_for_status()
        return data

    def iteration_generations():
        offset = 0
        limit = 100
        while True:
            response = generations(offset, limit)
            if len(response["generations"]) == 0:
                break
            for generation in response["generations"]:
                yield generation
            offset += limit

    def upload_to_s3(url, bucket_name, object_key, objects={}):
        response = requests.get(url)
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))

        if object_key not in objects:
            s3.put_object(Body=image_data, Bucket=bucket_name, Key=object_key)

        return image, len(image_data)

    def upload_and_resize(url, bucket_name, object_key, objects={}):
        response = requests.get(url)
        image_data = response.content

        image = Image.open(io.BytesIO(image_data))
        image.thumbnail((480, 480))

        output = io.BytesIO()
        image.save(output, format="JPEG")
        output.seek(0)
        size = len(output.getvalue())
        output.seek(0)
        if object_key not in objects:
            s3.upload_fileobj(output, bucket_name, object_key)

        return image, size

    s3_keys = {}
    existing = 0
    i = 0
    models = {}

    os.makedirs(username, exist_ok=True)

    for gen in iteration_generations():

        class Generation:
            def __init__(self, data):
                self.data = data
                self.generated_images = [
                    type(
                        "GeneratedImage",
                        (),
                        {
                            "url": img.get("url"),
                            "nsfw": img.get("nsfw"),
                            "id": img.get("id"),
                            "like_count": img.get("likeCount"),
                            "generated_image_variation_generics": img.get(
                                "generated_image_variation_generics", []
                            ),
                        },
                    )
                    for img in data.get("generated_images", [])
                ]
                self.model_id = data.get("modelId")
                self.prompt = data.get("prompt")
                self.negative_prompt = data.get("negativePrompt")
                self.image_height = data.get("imageHeight")
                self.image_width = data.get("imageWidth")
                self.inference_steps = data.get("inferenceSteps")
                self.seed = data.get("seed")
                self.is_public = data.get("public")
                self.scheduler = data.get("scheduler")
                self.sd_version = data.get("sdVersion")
                self.status = data.get("status")
                self.preset_style = data.get("presetStyle")
                self.init_strength = data.get("initStrength")
                self.guidance_scale = data.get("guidanceScale")
                self.id = data.get("id")
                self.created_at = datetime.datetime.strptime(
                    data.get("createdAt"), "%Y-%m-%dT%H:%M:%S.%f"
                )

        generation = Generation(gen)
        images = generation.generated_images

        metadata = copy(gen)
        metadata.pop("generated_images")

        for image in images:
            i += 1

            click.echo(f"{image.id} {generation.created_at}")
            dt = generation.created_at.strftime("%Y/%m/%d")

            existing_s3_objects = s3_keys.get(dt)
            if not existing_s3_objects:
                existing_s3_objects = {
                    x[0]: x[1]
                    for x in list_bucket(
                        s3,
                        bucket=bucket,
                        prefix=os.path.join(os.path.join(username, dt)),
                    )
                }
                s3_keys[dt] = existing_s3_objects
                for key in list(s3_keys):
                    if key[0:7] > dt[0:7]:
                        del s3_keys[key]

            exif = metadata
            if generation.model_id and generation.model_id not in models:
                model = get_model(generation.model_id)
                models[generation.model_id] = model

            exif["model"] = (
                models.get(generation.model_id, {})
                .get("custom_models_by_pk", {})
                .get("name", "Unknown")
            )

            data = {
                "uuid": image.id,
                "masterFingerprint": image.id,
                "original_filename": urlparse(image.url).path.split("/")[-1],
                "date": generation.created_at,
                "versions": [],
                "width": generation.image_width,
                "height": generation.image_height,
                "title": generation.prompt,
                "exif": exif,
                "library": "leonardo",
                "isphoto": True,
            }

            if image.generated_image_variation_generics:
                click.echo(image.generated_image_variation_generics)

            version = "medium"
            path = os.path.join(
                username, dt, data["uuid"], version, data["original_filename"]
            )
            _, size = upload_to_s3(image.url, bucket, path, {})
            data["versions"].append(
                dict(
                    version=version,
                    s3_path=path,
                    filename=data["original_filename"],
                    width=data["width"],
                    height=data["height"],
                    size=size,
                    type=path.split(".")[-1].lower(),
                )
            )

            thumb_key = path.replace(f"/{version}/", "/thumb/")
            uploaded_image, size = upload_and_resize(image.url, bucket, thumb_key, {})
            data["versions"].append(
                dict(
                    version="thumb",
                    s3_path=thumb_key,
                    filename=data["original_filename"],
                    width=uploaded_image.width,
                    height=uploaded_image.height,
                    size=size,
                    type=thumb_key.split(".")[-1].lower(),
                )
            )

            _, r = wrap(session, f"{base_url}/api/photos/", data, "POST")

            if r.status_code == 400 and "this uuid already exists" in r.text:
                existing += 1

                if existing > stop_after:
                    break

                _, r = wrap(
                    session,
                    f"{base_url}/api/photos/{data['uuid']}/",
                    data=data,
                    method="PATCH",
                )

            elif r.status_code > 399:
                click.echo(f"{r.status_code} {r.text}")
                r.raise_for_status()

    click.echo(f"{i + 1} photos, {existing} existing")
