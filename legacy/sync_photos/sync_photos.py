import concurrent.futures
import json
import os
from datetime import datetime, timedelta, timezone

import boto3
import osxphotos
import requests
from tools import DateTimeEncoder
from dateutil import parser

photos_db = osxphotos.PhotosDB()
base_path = photos_db.library_path
s3 = boto3.client("s3", "us-west-2")

bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")
base_url = os.environ.get("BASE_URL", "http://localhost:8000")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")

r = requests.post(
    f"{base_url}/api/auth/login", data={"username": username, "password": password}
)
r.raise_for_status()
token = r.json()["access_token"]

r = requests.get(f"{base_url}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
r.raise_for_status()
user = r.json()


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


def get_server_blocks():
    r = requests.get(
        f"{base_url}/photos/blocks", headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    return r.json()


total = 0


def populate_blocks():
    global total

    blocks = {}
    for photo in photos_db.photos():
        dt = photo.date.astimezone(timezone.utc)
        if not photo._info["cloudAssetGUID"]:
            # print(photo.uuid, photo.original_filename, photo.path, photo.path_edited, photo.path_live_photo, photo.path_raw, photo.path_derivatives)
            continue

        total = total + 1

        if dt.year not in blocks:
            blocks[dt.year] = {}

        if dt.month not in blocks[dt.year]:
            blocks[dt.year][dt.month] = {}

        if dt.day not in blocks[dt.year][dt.month]:
            blocks[dt.year][dt.month][dt.day] = []

        blocks[dt.year][dt.month][dt.day].append(photo)

    return blocks


def find_discrepancies(blocks, server_blocks):
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
                    print(f"discrepancy {year}/{month}/{day}, {vals} vs {count}/{date}")
                    photos_to_process.extend(blocks[year][month][day])

    return photos_to_process


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
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )

    if r.status_code == 404:
        return
    #     p["id"] = hash_id
    #     r = requests.post(
    #         f"{base_url}/api/photos/",
    #         data=json.dumps(p, cls=DateTimeEncoder),
    #         headers={
    #             "Content-Type": "application/json",
    #             "Authorization": f"Token {token}",
    #         },
    #     )
    # print(r.text)
    r.raise_for_status()
    # if r.status_code == 400:
    #    print(r.json(), p)

    # if r.status_code not in (200, 201):
    #     return
    # data = r.json()
    # updates = {}

    # base, ext = os.path.splitext(photo.path)
    # key = f"{username}/originals/{p['uuid'][0:1]}/{p['uuid']}{ext}"
    # if photo.path and data["s3_key_path"] is None:
    #     print(f"Uploading {key} to {bucket}")
    #     s3.upload_file(photo.path, bucket, key)
    #     updates["s3_key_path"] = key

    # is_modified = False
    # if data["date_modified"]:
    #     modified_date = parser.parse(data["date_modified"])
    #     is_modified = modified_date and modified_date > photo.date_modified

    # if photo.path_edited and (data["s3_edited_path"] is None or is_modified):
    #     base, ext = os.path.splitext(photo.path_edited)

    #     key = f"{username}/edited/{p['uuid'][0:1]}/{p['uuid']}{ext}"
    #     print(f"Uploading {key} to {bucket}")

    #     s3.upload_file(photo.path_edited, bucket, key)

    #     updates["s3_edited_path"] = key

    # if photo.path_derivatives:
    #     base, ext = os.path.splitext(photo.path_derivatives[-1])
    #     thumbnail_key = f"{username}/thumbnails/{p['uuid'][0:1]}/{p['uuid']}{ext}"

    #     if (
    #         data["s3_thumbnail_path"] is None
    #         or data["s3_thumbnail_path"] != thumbnail_key
    #         or is_modified
    #     ):
    #         print(f"Uploading {thumbnail_key} to {bucket}")
    #         s3.upload_file(photo.path_derivatives[-1], bucket, thumbnail_key)
    #         updates["s3_thumbnail_path"] = thumbnail_key

    # if updates:
    #     r = requests.patch(
    #         f'{base_url}/api/photos/{p["uuid"]}/',
    #         updates,
    #         headers={"Authorization": f"Token {token}"},
    #     )
    #     r.raise_for_status()

    # return updates


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
                "Authorization": f"Bearer {token}",
            },
        )

        if r.status_code == 404:
            r = requests.post(
                f"{base_url}/api/albums/",
                data=json.dumps(album, cls=DateTimeEncoder),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
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
    photos = {}
    for photo in photos_db.photos():
        p = photo.asdict()
        uuid = photo._info["cloudAssetGUID"] or photo.uuid

        if photo.path:
            base, ext = os.path.splitext(photo.path)
            key = f"{username}/originals/{uuid[0:1]}/{uuid}{ext}"
            photos[key] = (uuid, "s3_key_path")

        if photo.path_edited:
            base, ext = os.path.splitext(photo.path_edited)
            key = f"{username}/edited/{uuid[0:1]}/{uuid}{ext}"
            photos[key] = (uuid, "s3_edited_path")

        if photo.path_derivatives:
            base, ext = os.path.splitext(photo.path_derivatives[-1])
            thumbnail_key = f"{username}/thumbnails/{uuid[0:1]}/{uuid}{ext}"
            photos[thumbnail_key] = (uuid, "s3_thumbnail_path")

    rs = list_bucket(bucket=bucket, prefix=username)

    for i, (key, size, mod) in enumerate(rs):
        if i % 1000 == 0:
            print(i, key, size, mod)

        if not size:
            print(f"Deleting {key} for {photos.get(key)}")
            delete_uuid, k = photos.get(key, (None, None))

            s3.delete_object(Bucket=bucket, Key=key)

            if delete_uuid:
                r = requests.patch(
                    f"{base_url}/api/photos/{uuid}/",
                    {k: None},
                    headers={"Authorization": f"Bearer {token}"},
                )
                r.raise_for_status()


if __name__ == "__main__":
    blocks = populate_blocks()
    server_blocks = get_server_blocks()
    photos = find_discrepancies(blocks, server_blocks=server_blocks)

    print("total", total, "to process:", len(photos))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = executor.map(sync_photo, photos)

        results = list(futures)

        print(len(results), "checked", len(list(filter(None, results))), "uploaded")

    # upload_albums()
