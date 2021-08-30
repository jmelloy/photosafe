import concurrent.futures
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta

import boto3
import osxphotos
import requests
from dateutil import parser
from tools import DateTimeEncoder

photos_db = osxphotos.PhotosDB()
base_path = photos_db.library_path
s3 = boto3.client("s3", "us-west-2")

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

r = requests.get(
    f"{base_url}/photos/blocks", headers={"Authorization": f"Token {token}"}
)
r.raise_for_status()
server_blocks = r.json()
# print(server_blocks)


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


blocks = {}
total = 0


def populate_blocks():
    global blocks
    global total
    if not blocks:
        for total, photo in enumerate(photos_db.photos()):
            dt = photo.date

            if dt.year not in blocks:
                blocks[dt.year] = {}

            if dt.month not in blocks[dt.year]:
                blocks[dt.year][dt.month] = {}

            if dt.day not in blocks[dt.year][dt.month]:
                blocks[dt.year][dt.month][dt.day] = []

            blocks[dt.year][dt.month][dt.day].append(photo)


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

    # if r.status_code == 400:
    #    print(r.json(), p)

    if r.status_code not in (200, 201):
        return
    data = r.json()
    updates = {}

    if photo.path and data["s3_key_path"] is None:
        base, ext = os.path.splitext(photo.path)
        key = f"{username}/originals/{p['uuid'][0:1]}/{p['uuid']}{ext}"
        print(f"Uploading {key} to {bucket}")
        s3.upload_file(photo.path, bucket, key)
        updates["s3_key_path"] = key

    if photo.path_edited and data["s3_edited_path"] is None:
        base, ext = os.path.splitext(photo.path_edited)

        key = f"{username}/edited/{p['uuid'][0:1]}/{p['uuid']}{ext}"
        print(f"Uploading {key} to {bucket}")

        s3.upload_file(photo.path_edited, bucket, key)

        updates["s3_edited_path"] = key

    if photo.path_derivatives:
        base, ext = os.path.splitext(photo.path_derivatives[-1])
        thumbnail_key = f"{username}/thumbnail/{p['uuid'][0:1]}/{p['uuid']}{ext}"
        print(f"Uploading {thumbnail_key} to {bucket}")

        if (
            data["s3_thumbnail_path"] is None
            or data["s3_thumbnail_path"] != thumbnail_key
        ):
            s3.upload_file(photo.path_derivatives[-1], bucket, thumbnail_key)
            updates["s3_thumbnail_path"] = thumbnail_key

    if updates:
        r = requests.patch(
            f'{base_url}/api/photos/{p["uuid"]}/',
            updates,
            headers={"Authorization": f"Token {token}"},
        )
        r.raise_for_status()

    return updates


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

        if not album["photos"]:
            continue

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


def list_bucket(bucket, prefix=""):

    key = ""
    rs = {"IsTruncated": True}
    i = 0
    while rs["IsTruncated"]:
        rs = s3.list_objects(Bucket=bucket, Prefix=prefix, Marker=key)
        if not rs.get("Contents"):
            return
        for row in rs.get("Contents", []):
            key = row["Key"]
            i += 1
            yield (
                row["Key"],
                row.get("Size", 0),
                row["LastModified"],
            )
    print("%d rows returned for %s" % (i, prefix))


def cleanup(username):
    rs = list_bucket(bucket=bucket, prefix=username)

    photos = {}
    for photo in photos_db.photos():
        p = photo.asdict()
        uuid = photo._info["cloudAssetGUID"] or photo.uuid

        if photo.path:
            base, ext = os.path.splitext(photo.path)
            key = f"{username}/originals/{p['uuid'][0:1]}/{p['uuid']}{ext}"
            photos[key] = (uuid, "s3_key_path")

        if photo.path_edited:
            base, ext = os.path.splitext(photo.path_edited)
            key = f"{username}/edited/{p['uuid'][0:1]}/{p['uuid']}{ext}"
            photos[key] = (uuid, "s3_edited_path")

        if photo.path_derivatives:
            base, ext = os.path.splitext(photo.path_derivatives[-1])
            thumbnail_key = f"{username}/thumbnail/{p['uuid'][0:1]}/{p['uuid']}{ext}"
            photos[thumbnail_key] = (uuid, "s3_thumbnail_path")

    for (key, size, mod) in rs:
        if not size:
            delete_uuid, k = photos.get(key)

            print(f"Deleting {key} for {delete_uuid}")
            s3.delete_object(Bucket=bucket, Key=key)

            r = requests.patch(
                f"{base_url}/api/photos/{uuid}/",
                {k: None},
                headers={"Authorization": f"Token {token}"},
            )
            r.raise_for_status()


if __name__ == "__main__":

    populate_blocks()
    photos_to_process = []
    for year, months in blocks.items():
        for month, days in months.items():
            for day, photos in days.items():
                count = len(photos)
                date = max([x.date_modified or x.date for x in photos])
                vals = (
                    server_blocks.get(str(year), {})
                    .get(str(month), {})
                    .get(str(day), {})
                )

                if (
                    not vals
                    or vals["count"] != count
                    or abs(parser.parse(vals["max_date"]) - date) > timedelta(seconds=3)
                ):
                    print(f"discrepancy {year}/{month}/{day}, {vals} vs {count}/{date}")
                    photos_to_process.extend(blocks[year][month][day])

    print("total", total, "to process:", len(photos_to_process))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(sync_photo, photos_db.photos())

        results = list(futures)

        print(len(results), "checked", len(list(filter(None, results))), "uploaded")

    upload_albums()
