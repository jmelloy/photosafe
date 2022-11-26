import os
import sys
from pyicloud import PyiCloudService
import boto3
import requests
import json
from tools import DateTimeEncoder
import shutil
import hashlib
import datetime
import pytz

s3 = boto3.client(
    "s3",
    "us-west-2",
    aws_access_key_id="",
    aws_secret_access_key="",
)

bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")
base_url = os.environ.get("BASE_URL", "http://localhost:8000")
username = os.environ.get("USERNAME", "jmelloy")
password = os.environ.get("PASSWORD", "invasion")

r = requests.post(
    f"{base_url}/auth-token/", json={"username": username, "password": password}
)
r.raise_for_status()
token = r.json()["token"]

r = requests.get(f"{base_url}/users/me", headers={"Authorization": f"Token {token}"})
r.raise_for_status()
user = r.json()

type_mapping = {
    "com.apple.quicktime-movie": "mov",
    "public.jpeg": "jpeg",
    "public.heic": "heic",
    "public.png": "png",
    "public.mpeg-4": "mov",
}

username = input("Username: ")
password = input("Password: ")

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


def upload_photo(photo, version, path):
    os.makedirs(os.path.split(path)[0], exist_ok=True)
    with open(path, "wb") as FILE:
        r = photo.download(version)
        FILE.write(r.raw.read())

    s3.upload_file(path, bucket, path)
    os.remove(path)


if __name__ == "__main__":
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

        r = requests.post(
            f"{base_url}/api/photos/",
            data=json.dumps(data, cls=DateTimeEncoder),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {token}",
            },
        )

        if r.status_code == 400 and "this uuid already exists" in r.text:
            r = requests.patch(
                f"{base_url}/api/photos/{data['uuid']}/",
                data=json.dumps(data, cls=DateTimeEncoder),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Token {token}",
                },
            )

        if r.status_code > 399:
            print(r.status_code, r.text)
            r.raise_for_status()

        if photo.asset_date < datetime.datetime(2022, 11, 1, tzinfo=pytz.utc):
            break

    shutil.rmtree(username)
