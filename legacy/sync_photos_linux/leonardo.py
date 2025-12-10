import argparse
import datetime
import io
import json
import logging
import os
from copy import copy
from urllib.parse import urlparse

import boto3
import requests
from PIL import Image
from tools import DateTimeEncoder, list_bucket
from tqdm import tqdm

logging.basicConfig(
    format="%(asctime)s %(levelname)6s %(message)s",
    datefmt="%b %d %H:%M:%S",
)

logger = logging.getLogger()


class GeneratedImage:
    def __init__(self, data):
        self.url = data.get("url")
        self.nsfw = data.get("nsfw")
        self.id = data.get("id")
        self.like_count = data.get("likeCount")
        self.generated_image_variation_generics = data.get(
            "generated_image_variation_generics", []
        )


class Generation:
    def __init__(self, data):
        self.data = data

        self.generated_images = [
            GeneratedImage(image_data)
            for image_data in data.get("generated_images", [])
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


s3 = boto3.client(
    "s3",
    "us-west-2",
)

bucket = os.environ.get("BUCKET", "jmelloy-photo-backup")
base_url = os.environ.get("BASE_URL", "https://api.photosafe.melloy.life")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")

KEY = "7b66ba15-e896-4368-b25c-0570bef4abaa"

r = requests.post(
    f"{base_url}/api/auth/login", data={"username": username, "password": password}
)
r.raise_for_status()
token = r.json()["access_token"]

r = requests.get(f"{base_url}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
r.raise_for_status()
user = r.json()

leonardo_key = os.environ.get("LEONARDO_KEY") or input("Key: ")

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {token}"})
session.headers.update({"Content-Type": f"application/json"})

leonardo_session = requests.Session()
leonardo_session.headers.update({"Authorization": f"Bearer {leonardo_key}"})
leonardo_session.headers.update({"Accept": f"application/json"})

user_details = {
    "user_details": [
        {
            "user": {
                "id": "278a9059-6820-4882-aec1-a02d0c7867af",
                "username": "jmelloy",
            },
            "tokenRenewalDate": "2023-07-25T00:00:00",
            "subscriptionTokens": 8308,
            "subscriptionGptTokens": 1000,
            "subscriptionModelTokens": 10,
            "apiCredit": 1,
        }
    ]
}


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
        resp = session.delete(
            f"{url}",
        )
    elif method.upper() == "PATCH":
        resp = session.patch(
            f"{url}",
            data=json.dumps(data, cls=DateTimeEncoder),
        )

    end = datetime.datetime.now()

    logger.info(f""" --> {resp.status_code} - {end - start}""")

    logger.debug(f"{json.dumps(resp.json(), indent=2)}")

    if resp.status_code > 205:
        logger.warning(resp.text)

    # resp.raise_for_status()
    return resp.json(), resp


def get_model(id: str) -> dict:
    url = f"https://cloud.leonardo.ai/api/rest/v1/models/{id}"

    data, r = wrap(leonardo_session, url, {}, "GET")
    r.raise_for_status()
    return data


def generations(offset, limit, user_id="278a9059-6820-4882-aec1-a02d0c7867af") -> dict:
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

    if not object_key in objects:
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
    if not object_key in objects:
        s3.upload_fileobj(output, bucket_name, object_key)

    return image, size


if __name__ == "__main__":
    s3_keys = {}
    existing = 0

    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-after", type=int, default=5)

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set the log level",
    )
    args = parser.parse_args()

    logger.setLevel(getattr(logging, args.log_level.upper()))
    i = 0

    models = {}

    os.makedirs(username, exist_ok=True)
    for gen in iteration_generations():
        generation = Generation(gen)

        images = generation.generated_images

        metadata = copy(gen)
        metadata.pop("generated_images")

        for image in images:
            i += 1

            print(image.id, generation.created_at)
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
                # print(sys.getsizeof(), "bytes")

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
                print(image.generated_image_variation_generics)

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

                if existing > args.stop_after:
                    break

                _, r = wrap(
                    session,
                    f"{base_url}/api/photos/{data['uuid']}/",
                    data=data,
                    method="PATCH",
                )

            elif r.status_code > 399:
                print(r.status_code, r.text)
                r.raise_for_status()

    print(i + 1, " photos", existing, " existing")
