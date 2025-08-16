import json
import time
import os
import requests
from urllib.parse import quote
import logging
from datetime import datetime
from convert_to_xmp import create_xmp_metadata
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
API_QUERY_GENERATED_IMAGES = (
    "https://civitai.com/api/trpc/orchestrator.queryGeneratedImages"
)
API_MODELS = "https://civitai.com/api/v1/models"
DATA_RATE_LIMIT = 100  # milliseconds
IMAGE_RATE_LIMIT = 100  # milliseconds
MAX_ATTEMPTS = 10

# Headers
shared_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://civitai.com/",
}

json_headers = {"Content-Type": "application/json", "Accept": "application/json"}

image_headers = {"Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"}


# Util functions
def wait(ms):
    time.sleep(ms / 1000)


def get_generations(token, cursor, tags=None):
    if tags is None:
        tags = []

    headers_to_use = {**shared_headers, **json_headers}
    headers_to_use["Authorization"] = f"Bearer {token}"

    input_params = {"json": {"authed": True, "tags": ["gen"] + tags}}
    if cursor:
        input_params["json"]["cursor"] = cursor

    input_query = quote(json.dumps(input_params))
    url = f"{API_QUERY_GENERATED_IMAGES}?input={input_query}"

    response = requests.get(url, headers=headers_to_use)
    response.raise_for_status()
    return response.json()


def get_all_generations(token, cursor, tags=None):
    attempts = 0
    while True:
        try:
            data = get_generations(token, cursor, tags)
            logger.debug(json.dumps(data))
            logger.info(
                f"Fetched {len(data['result']['data']['json']['items'])} generations"
            )
            attempts = 0

            for generation in data["result"]["data"]["json"]["items"]:
                yield generation

            if cursor := data["result"]["data"]["json"].get("nextCursor"):
                wait(DATA_RATE_LIMIT)
            else:
                return
        except Exception as e:
            attempts += 1
            logger.error(f"Error fetching generations: {e}")
            wait(1000)
            if attempts >= MAX_ATTEMPTS:
                return


def fetch_image(url):
    global previous_fetch
    now = int(time.time() * 1000)

    if previous_fetch and (now - previous_fetch) < IMAGE_RATE_LIMIT:
        wait(IMAGE_RATE_LIMIT - (now - previous_fetch))
        now = int(time.time() * 1000)

    previous_fetch = now

    try:
        response = requests.get(
            url, headers={**shared_headers, **image_headers}, stream=True
        )
        if response.status_code == 200:
            return response.content
    except Exception:
        return None

    return None


def fetch_model(model_id):
    url = f"{API_MODELS}/{model_id}"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def fetch_file(url, filepath, token):
    headers = {}

    headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 404:
        logger.warning(f"File not found: {url}")
        return

    response.raise_for_status()

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)


def write_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f)


def update_metadata():
    for root, dirs, files in os.walk("generations"):
        if not dirs:
            continue

        for file in files:
            if file == "metadata.json":
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    generation_data = json.load(f)
                    for step in generation_data["steps"]:
                        step_path = f"{root}/{step['name']}"
                        for image in step.get("images", []):
                            image_metadata_path = f"{step_path}/{image['id']}.json"
                            with open(image_metadata_path, "r") as F:
                                image_data = json.load(F)
                            image_data.update(step.get("params"))
                            sidecar = create_xmp_metadata(image_data)
                            with open(f"{step_path}/{image['id']}.xmp", "w") as f:
                                f.write(sidecar)


if __name__ == "__main__":
    update_metadata()

    civitai_token = os.getenv("CIVITAI_API_TOKEN") or input(
        "Enter your Civitai API token: "
    )

    # Fetch generations
    prev_date = None
    for generation in get_all_generations(civitai_token, None):
        logger.debug(generation)
        date_str = datetime.strptime(
            generation["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).strftime("%Y-%m-%d")
        base_path = f"generations/{date_str}/{generation['id']}"
        write_json(generation, f"{base_path}/metadata.json")

        if prev_date != date_str:
            logger.info(f"Processing {date_str}")
            prev_date = date_str

        for step in generation["steps"]:
            step_path = f"{base_path}/{step['name']}"

            write_json(step, f"{step_path}/metadata.json")
            logger.info(f"Prompt: {step['params']['prompt'][:100]}")

            for image in step.get("images", []):
                url = image["url"]
                image.update(step.get("params", {}))

                if not os.path.exists(f"{step_path}/{image['id']}"):
                    logger.info(f"Fetching image {image['id']}")
                    filepath = f"{step_path}/{image['id']}"
                    fetch_file(url, filepath, civitai_token)

                write_json(image, f"{step_path}/{image['id']}.json")
                sidecar = create_xmp_metadata(image)
                write_json(sidecar, f"{step_path}/{image['id']}.xmp")
