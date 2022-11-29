import datetime
import os
import sys
import tempfile

import boto3
from config import celery_app
from django.db import IntegrityError
from pyicloud import PyiCloudService

from photosafe.photos.models import Photo, Version

bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")

s3 = boto3.client(
    "s3",
    "us-west-2",
    aws_access_key_id="AKIARWSV2L5TCXZ5AHK4",
    aws_secret_access_key="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",
)

username = "jmelloy@gmail.com"
password = "AshleyGeoriga24Apple"

api = PyiCloudService(username, password)

if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print(
                "Failed to request trust. You will likely be prompted for the code again in the coming weeks"
            )
elif api.requires_2sa:
    import click

    print("Two-step authentication required. Your trusted devices are:")

    devices = api.trusted_devices
    for i, device in enumerate(devices):
        print(
            "  %s: %s"
            % (i, device.get("deviceName", "SMS to %s" % device.get("phoneNumber")))
        )

    device = click.prompt("Which device would you like to use?", default=0)
    device = devices[device]
    if not api.send_verification_code(device):
        print("Failed to send verification code")
        sys.exit(1)

    code = click.prompt("Please enter validation code")
    if not api.validate_verification_code(device, code):
        print("Failed to verify verification code")
        sys.exit(1)


def photo_ref(api):
    m = {}
    prev = datetime.datetime.now().strftime("%Y-%m")
    for i, photo in enumerate(api.photos.all):
        m[photo._asset_record["recordName"]] = photo
        if photo.asset_date.strftime("%Y-%m") != prev:
            print(i, prev, photo)
        prev = photo.asset_date.strftime("%Y-%m")
    return m


@celery_app.task()
def upload_version(photo, version, path):
    tf = tempfile.NamedTemporaryFile(delete=False)
    r = photo.download(version)
    tf.write(r.raw.read())
    tf.close()

    s3.upload_file(tf.name, bucket, path)
    os.unlink(tf.name)

    Version.create(photo_uuid=photo._asset_record["recordName"], **version)


@celery_app.task()
def sync_photos():
    for i, photo in enumerate(api.photos.all):
        print(photo, photo.created)
        dt = (photo.asset_date or photo.created).strftime("%Y/%m/%D")

        data = {
            "uuid": photo._asset_record["recordName"],  # cloudAssetGUID
            "masterFingerprint": photo.id,
            "original_filename": photo.filename,
            "date": photo.asset_date or photo.created,
            "versions": [],
            "size": photo.versions["original"]["size"],
            "uti": photo.versions["original"]["type"],
            "width": photo.versions["original"]["width"],
            "height": photo.versions["original"]["height"],
            "hidden": photo.isHidden,
            "favorite": photo.isFavorite,
            "title": photo.caption,
            "description": photo.description,
            "latitude": photo.latitude,
            "longitude": photo.longitude,
            "exif": photo.mediaMetaData.get("{Exif}"),
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
            upload_version.delay(photo, version, path)

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
                )
            )

        data.update(
            {
                k: v["value"]
                for (k, v) in photo._asset_record["fields"].items()
                if type(v["value"]) != dict
            }
        )
        data.update(
            {
                k: v["value"]
                for (k, v) in photo._master_record["fields"].items()
                if type(v["value"]) != dict
            }
        )
        try:
            photo = Photo.create(**data)
        except IntegrityError:
            break
