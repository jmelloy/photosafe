import requests
import logging
import json
import os
import datetime
from json import JSONEncoder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()


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

    resp.raise_for_status()
    return resp.json(), resp


token = "eyJraWQiOiJtM1IxVnh4VWlEa1Q3Z1lrc3dYWlBFb1JEcnRWU0E0M3E0bUtzc29ZWWpZPSIsImFsZyI6IlJTMjU2In0.eyJhdF9oYXNoIjoiUEtCdHdHWG5paXd0SEx0eElVeUgyZyIsInN1YiI6ImI5OGU2M2Y4LTllZGMtNGJkNC04YWQ0LTQ1NjRjNWVkNGQwMCIsImNvZ25pdG86Z3JvdXBzIjpbInVzLWVhc3QtMV94a1ZNdUNxZXVfR29vZ2xlIl0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaHR0cHM6XC9cL2hhc3VyYS5pb1wvand0XC9jbGFpbXMiOiJ7XCJ4LWhhc3VyYS11c2VyLWlkXCI6XCIyNzhhOTA1OS02ODIwLTQ4ODItYWVjMS1hMDJkMGM3ODY3YWZcIixcIngtaGFzdXJhLWRlZmF1bHQtcm9sZVwiOlwidXNlclwiLFwieC1oYXN1cmEtYWxsb3dlZC1yb2xlc1wiOltcInVzZXJcIl19IiwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfeGtWTXVDcWV1IiwiY29nbml0bzp1c2VybmFtZSI6Imdvb2dsZV8xMDM1NDE3NTI5NjM2MjY2NDg0MzAiLCJnaXZlbl9uYW1lIjoiSmVmZnJleSIsIm5vbmNlIjoib1VqNUE5cHJWNTlKMGZCclpIYk9XVE9UWG1wQTg0TWNjdXlSYUs2ZHN2QSIsIm9yaWdpbl9qdGkiOiJmOGFjM2FjNC1lMjNiLTRiNDQtOTkyZS02MTg1YmIwNDVhNTgiLCJhdWQiOiI5c2ExZGxoNmo0dTZlNGZpdjFjMTI0NHBxIiwiaWRlbnRpdGllcyI6W3sidXNlcklkIjoiMTAzNTQxNzUyOTYzNjI2NjQ4NDMwIiwicHJvdmlkZXJOYW1lIjoiR29vZ2xlIiwicHJvdmlkZXJUeXBlIjoiR29vZ2xlIiwiaXNzdWVyIjpudWxsLCJwcmltYXJ5IjoidHJ1ZSIsImRhdGVDcmVhdGVkIjoiMTY4MjI3NzI1MDMxNyJ9XSwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3MzYxODIyMjcsIm5hbWUiOiJKZWZmcmV5IE1lbGxveSIsImN1c3RvbTpzdWIiOiIxMDM1NDE3NTI5NjM2MjY2NDg0MzAiLCJleHAiOjE3MzYxODU4MjcsImlhdCI6MTczNjE4MjIyNywiZmFtaWx5X25hbWUiOiJNZWxsb3kiLCJqdGkiOiI0OTkzMzBiNC02ZWNhLTRiNjQtYTNlNC1hZDY2MzEzMDkwMzgiLCJlbWFpbCI6ImptZWxsb3lAZ21haWwuY29tIn0.hmdo_FaxxcvyeoeSKa3swz8m9VqXAcLmpv6VIoNMmflyBNYpZThTkjKKiAygBZy_KvU2beVB4rfKXWYlt0X604hrPEQ8-rKw9kR54MapYOvB6ntZie1AHEZlRRO4KR6ubomuxJ4um2YFRczJUdLdXV4oIaKlF-O4cLU76oeN9aCUPRSBEo4yV4Hba5togma9WFilxHc8vPH-VGTU6364z-F_HO4R6FGTYEkIIiGC4cLPfiqnn8TFjyhUD3zaGHb86Yo0WIVDITSkro1syK1l1HjEGANFaL5cbVEIkaKsv2iMEkzt44BJ54GgBBi7AUfmM1cYS0FXLaDi-sGKxFl7Wg"

request = {
    "operationName": "GetFeedImages",
    "variables": {
        "order_by": [{}, {"createdAt": "desc"}],
        "where": {
            "createdAt": {"_lt": "2025-01-06T16:52:05.689Z"},
            "generation": {
                "status": {"_eq": "COMPLETE"},
                "canvasRequest": {"_eq": False},
                "category": {},
                "isStoryboard": {"_eq": False},
            },
            "userId": {"_eq": "278a9059-6820-4882-aec1-a02d0c7867af"},
            "teamId": {"_is_null": True},
        },
        "limit": 50,
        "userId": "278a9059-6820-4882-aec1-a02d0c7867af",
        "isLoggedIn": True,
    },
    "query": "query GetFeedImages($where: generated_images_bool_exp, $limit: Int, $userId: uuid, $isLoggedIn: Boolean!, $order_by: [generated_images_order_by!] = [{createdAt: desc}], $offset: Int) {\n  generated_images(\n    where: $where\n    limit: $limit\n    order_by: $order_by\n    offset: $offset\n  ) {\n    ...FeedParts\n    __typename\n  }\n}\n\nfragment FeedParts on generated_images {\n  createdAt\n  trendingScore\n  likeCount\n  id\n  url\n  nsfw\n  motionMP4URL\n  motionGIFURL\n  public\n  userId\n  teamId\n  ... @include(if: $isLoggedIn) {\n    ...UserLikedGeneratedImages\n    __typename\n  }\n  ...GeneratedImageModeration\n  user {\n    username\n    id\n    __typename\n  }\n  generation {\n    id\n    alchemy\n    contrastRatio\n    highResolution\n    prompt\n    negativePrompt\n    imageWidth\n    imageHeight\n    sdVersion\n    modelId\n    coreModel\n    guidanceScale\n    inferenceSteps\n    seed\n    scheduler\n    tiling\n    highContrast\n    promptMagic\n    promptMagicVersion\n    imagePromptStrength\n    prompt_moderations {\n      moderationClassification\n      __typename\n    }\n    custom_model {\n      id\n      name\n      userId\n      modelHeight\n      modelWidth\n      __typename\n    }\n    generation_elements {\n      id\n      lora {\n        akUUID\n        name\n        description\n        urlImage\n        baseModel\n        weightDefault\n        weightMin\n        weightMax\n        __typename\n      }\n      weightApplied\n      __typename\n    }\n    generation_controlnets(order_by: {controlnetOrder: asc}) {\n      id\n      weightApplied\n      controlnet_definition {\n        akUUID\n        displayName\n        displayDescription\n        controlnetType\n        __typename\n      }\n      controlnet_preprocessor_matrix {\n        id\n        preprocessorName\n        __typename\n      }\n      __typename\n    }\n    initStrength\n    category\n    public\n    teamId\n    nsfw\n    photoReal\n    imageToImage\n    __typename\n  }\n  collection_images {\n    id\n    __typename\n  }\n  generated_image_variation_generics(order_by: [{createdAt: desc}]) {\n    url\n    id\n    status\n    transformType\n    upscale_details {\n      id\n      alchemyRefinerCreative\n      alchemyRefinerStrength\n      oneClicktype\n      __typename\n    }\n    __typename\n  }\n  likeCount\n  __typename\n}\n\nfragment UserLikedGeneratedImages on generated_images {\n  user_liked_generated_images(limit: 1, where: {userId: {_eq: $userId}}) {\n    generatedImageId\n    __typename\n  }\n  __typename\n}\n\nfragment GeneratedImageModeration on generated_images {\n  generated_image_moderation {\n    moderationClassification\n    __typename\n  }\n  __typename\n}",
}


def yield_images():
    r = requests.Session()
    r.headers.update(
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
    )
    url = "https://api.leonardo.ai/v1/graphql"

    seen = True
    last_date = datetime.datetime.now()
    while seen:
        seen = False
        request["variables"]["where"]["createdAt"]["_lt"] = last_date

        json, _ = wrap(r, url, data=request)

        for image in json["data"]["generated_images"]:
            yield image
            last_date = image["createdAt"]
            seen = True


def organize_images():
    for dir, _, files in os.walk("output/leonardo"):
        if "meta.json" in files:
            with open(os.path.join(dir, "meta.json")) as f:
                meta = json.load(f)
                base = os.path.join(
                    "output",
                    "leonardo",
                    meta["user"]["username"],
                    meta["createdAt"].split("T")[0].replace("-", "/"),
                    meta["id"],
                )
                if not os.path.exists(base):
                    os.makedirs(base, exist_ok=True)

            for file in files:
                filename = os.path.join(base, file)

                if not os.path.exists(filename):
                    os.rename(os.path.join(dir, file), filename)


def main():
    for image in yield_images():
        print(image["createdAt"], image["url"].split("/")[-1])

        filename = os.path.join(
            "output",
            "leonardo",
            image["user"]["username"],
            image["createdAt"].split("T")[0].replace("-", "/"),
            image["id"],
            image["url"].split("/")[-1],
        )

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "wb") as f:
            f.write(requests.get(image["url"]).content)

        with open(os.path.join(os.path.dirname(filename), "meta.json"), "w") as f:
            f.write(json.dumps(image, indent=2))


if __name__ == "__main__":
    main()
