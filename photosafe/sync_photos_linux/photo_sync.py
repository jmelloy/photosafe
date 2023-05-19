import json
import os
import shutil
import sys
from collections import defaultdict
import pytz
import datetime
import mimetypes
from tqdm import tqdm

import boto3
import requests
from pyicloud import PyiCloudService
from tools import DateTimeEncoder, list_bucket

import argparse

s3 = boto3.client(
    "s3",
    "us-west-2",
)

bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")
base_url = os.environ.get("BASE_URL", "https://api.photosafe.melloy.life")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")

r = requests.post(
    f"{base_url}/auth-token/", json={"username": username, "password": password}
)
r.raise_for_status()
token = r.json()["token"]

r = requests.get(f"{base_url}/users/me", headers={"Authorization": f"Token {token}"})
r.raise_for_status()
user = r.json()

icloudUsername = os.environ.get("ICLOUD_USERNAME") or input("Username: ")
icloudPassword = os.environ.get("ICLOUD_PASSWORD") or input("Password: ")
api = PyiCloudService(icloudUsername, icloudPassword)

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
    r = photo.download(version)
    r.raise_for_status()
    size = photo.versions[version]["size"]

    with open(path, "wb") as FILE:
        shutil.copyfileobj(r.raw, FILE)

    # print(f"Uploading {path} to {bucket} ({size} b")

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
    print(f"Loading album {album_name}")
    for photo in api.photos.albums.get(album_name, []):
        photos.append(photo.id)
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

        r = requests.put(
            f"{base_url}/api/albums/{album.id}/",
            data=json.dumps(album_info, cls=DateTimeEncoder),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {token}",
            },
        )

        if r.status_code == 404:
            r = requests.post(
                f"{base_url}/api/albums/",
                data=json.dumps(album_info, cls=DateTimeEncoder),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Token {token}",
                },
            )

        if r.status_code >= 400:
            print(r.json(), album_info)
        # r.raise_for_status()


if __name__ == "__main__":
    s3_keys = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-after", type=int, default=100)

    args = parser.parse_args()
    os.makedirs(username, exist_ok=True)
    for library_name, album in api.photos.libraries.items():
        print(f"Library: {library_name}")
        existing = 0

        for i, photo in enumerate(album.all):
            print(photo, photo.created)
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
                # print(sys.getsizeof(), "bytes")

            exif = None
            meatadata = photo.mediaMetaData
            if meatadata:
                exif = meatadata.get("{Exif}")

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
                    )
                )

            # data.update(
            #     {
            #         k: v["value"]
            #         for (k, v) in photo._asset_record["fields"].items()
            #         if type(v["value"]) != dict
            #     }
            # )
            # data.update(
            #     {
            #         k: v["value"]
            #         for (k, v) in photo._master_record["fields"].items()
            #         if type(v["value"]) != dict
            #     }
            # )

            r = requests.post(
                f"{base_url}/api/photos/",
                data=json.dumps(data, cls=DateTimeEncoder),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Token {token}",
                },
            )

            if r.status_code == 400 and "this uuid already exists" in r.text:
                existing += 1

                if existing > args.stop_after:
                    break

                r = requests.patch(
                    f"{base_url}/api/photos/{data['uuid']}/",
                    data=json.dumps(data, cls=DateTimeEncoder),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Token {token}",
                    },
                )

            elif r.status_code > 399:
                print(r.status_code, r.text)
                r.raise_for_status()

        shutil.rmtree(username)
        print(i + 1, " photos", existing, " existing")
        upload_albums()
