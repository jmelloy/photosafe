import osxphotos

import concurrent.futures
import boto3
import botocore.exceptions
import requests
import json
from collections import defaultdict
import os
from tools import DateTimeEncoder

photos_db = osxphotos.PhotosDB()
base_path = photos_db.library_path
s3 = boto3.client("s3", "us-west-2")


bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")
base_url = os.environ.get("BASE_URL", "http://localhost:3000")
username = os.environ.get("USERNAME", "jmelloy")
password = os.environ.get("PASSWORD", "invasion")

r = requests.post(
    f"{base_url}/auth-token/", json={"username": username, "password": password}
)
token = r.json()["token"]


def build_album_list():
    album_keys = [
        "uuid",
        "creation_date",
        "end_date",
        "folder_list",
        "folder_names",
        "start_date",
        "title",
    ]
    photo_keys = [
        "uuid",
        "filename",
        "original_filename",
        "date",
        "description",
        "title",
        "keywords",
        "labels",
        "albums",
        "path",
        "path_edited",
    ]
    albums = {}

    for a in photos_db.album_info:
        album = dict([(k, getattr(a, k)) for k in album_keys])
        album["photos"] = [
            dict([(k, getattr(p, k)) for k in photo_keys]) for p in a.photos
        ]

        for p in album["photos"]:
            for k, v in p.items():
                if v and type(v) is str and base_path in v:
                    p[k] = v.replace(base_path, "")

        if a.title in albums:
            raise Exception("Duplicate album name %s" % a.title)
        albums[a.title] = album

    return albums


blocks = defaultdict(list)


def populate_blocks():
    global blocks
    if not blocks:
        for checked, photo in enumerate(photos_db.photos()):
            blocks[photo.date.date()].append(photo)


def determine_blocks(year, month=None, day=None):
    if not blocks:
        populate_blocks()

    ret = []
    for b in blocks:
        if b.year == year:
            if not month or b.month == month:
                if not day or b.day == day:
                    ret.extend(blocks[b])
    return ret


def count_blocks(level="year"):
    if not blocks:
        populate_blocks()

    counter = defaultdict(int)
    for b, v in blocks.items():
        counter[
            (
                str(b.year),
                b.strftime("%m") if level in ("month", "day") else "01",
                b.strftime("%d") if level in ("day") else "01",
            )
        ] += len(v)
    return sorted([["-".join(k), v] for k, v in counter.items()])


def sync_photo(photo):
    p = photo.asdict()
    p["masterFingerprint"] = photo._info["masterFingerprint"]
    if not photo._info["masterFingerprint"]:
        return

    p["uuid"] = photo._info["cloudAssetGUID"] or photo.uuid
    for k, v in p.items():
        if v and type(v) is str and base_path in v:
            p[k] = v.replace(base_path, "")

    r = requests.put(
        f"{base_url}/api/photos/{p['uuid']}/",
        data=json.dumps(p, cls=DateTimeEncoder),
        headers={"Content-Type": "application/json", "Authorization": f"Token {token}"},
    )

    if r.status_code == 404:
        r = requests.post(
            f"{base_url}/api/photos/",
            data=json.dumps(p, cls=DateTimeEncoder),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {token}",
            },
        )

    #if r.status_code == 400:
    #    print(r.json(), p)

    if r.status_code not in (200, 201):
        return

    key = None

    if photo.path and r.json()["s3_key_path"] is None:
        base, ext = os.path.splitext(photo.path)
        key = f"{username}/originals/{p['uuid'][0:1]}/{p['uuid']}{ext}"
        try:
            source_key=p['path'].strip("/")
            s3.copy_object(
                Bucket=bucket,
                CopySource=f"jmelloy-photo-backup/{source_key}",
                Key=key,
            )
            # s3.delete_object(Bucket=bucket, key=source_key)
        except botocore.exceptions.ClientError as e:
            print(e)
            if "NoSuchKey" in str(e):
                print(f"Uploading {photo.path} to {key}")
                s3.upload_file(photo.path, bucket, key)
            else:
                raise
        r = requests.patch(
            f'{base_url}/api/photos/{p["uuid"]}/',
            {"s3_key_path": key},
            headers={"Authorization": f"Token {token}"},
        )
        r.raise_for_status()

    if photo.path_edited and r.json()["s3_edited_path"] is None:
        key = f"{username}/edited/{p['uuid'][0:1]}/{p['uuid']}{ext}"
        s3.upload_file(photo.path_edited, bucket, key)

        r = requests.patch(
            f'{base_url}/api/photos/{p["uuid"]}/',
            {"s3_edited_path": key},
            headers={"Authorization": f"Token {token}"},
        )
        r.raise_for_status()

    return key


def upload_albums():
    for album_info in photos_db.album_info:
        album = {
            "uuid": album_info.uuid,
            "title": album_info.title,
            "creation_date": album_info.creation_date,
            "end_date": album_info.end_date,
            "start_date": album_info.start_date,
        }
        album["photos"] = list(
            map(
                lambda photo: photo._info["cloudAssetGUID"] or photo.uuid,
                album_info.photos,
            )
        )

        r = requests.put(
            f"{base_url}/api/albums/{album_info.uuid}/",
            data=json.dumps(album, cls=DateTimeEncoder),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {token}",
            },
        )

        if r.status_code == 404:
            r = requests.post(
                f"{base_url}/api/albums/",
                data=json.dumps(album, cls=DateTimeEncoder),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Token {token}",
                },
            )

        if r.status_code >= 400:
            print(r.json(), album)
            # r.raise_for_status()


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(sync_photo, photos_db.photos())

        results = list(futures)

        print(len(results), "checked", len(list(filter(None, results))), "uploaded")

    upload_albums()
