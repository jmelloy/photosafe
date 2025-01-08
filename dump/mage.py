import requests
import logging
import json
import os
import datetime
from json import JSONEncoder
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

l = logging.getLogger("urllib3")
l.setLevel(logging.WARNING)

logging.basicConfig(level=logging.DEBUG)


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
            json=data,
        )

    end = datetime.datetime.now()

    logger.info(f""" --> {resp.status_code} - {end - start}""")

    # logger.debug(resp.text)

    if resp.status_code > 205:
        logger.warning(resp.text)

    resp.raise_for_status()
    return resp.text, resp


def extract_braces(html_content):
    open = 0
    r = []
    output = []
    for el in html_content:
        if el == "{":
            open += 1
        if open > 0:
            r.append(el)
        if el == "}":
            open -= 1
        if open == 0 and r:
            output.append("".join(r))
            r = []
    return output


def yield_images():
    cookie = "ph_phc_lBVvvz084lS4XFbPqGf38TGEa6HnGhmgVHcf4f0NNuX_posthog=%7B%22distinct_id%22%3A%22dgGk4FOcMSf5KbIBqkQAteJolLB3%22%2C%22%24sesid%22%3A%5B1736184372001%2C%2201943ca6-eb4f-79c2-8306-9110b8f6ae65%22%2C1736184359759%5D%2C%22%24epp%22%3Atrue%7D; __session=eyJhbGciOiJSUzI1NiIsImtpZCI6Ii1XWnBLUSJ9.eyJpc3MiOiJodHRwczovL3Nlc3Npb24uZmlyZWJhc2UuZ29vZ2xlLmNvbS9tYWdlZG90c3BhY2UiLCJuYW1lIjoiSmVmZnJleSBNZWxsb3kiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSkV1TjNHamtHRWZucG9zNFlXcVhkdHB6cUxTbi0wb3dZZUpDVmhZSURpbEFcdTAwM2RzOTYtYyIsInN0cmlwZVJvbGUiOiJwcm9fcGx1cyIsImF1ZCI6Im1hZ2Vkb3RzcGFjZSIsImF1dGhfdGltZSI6MTczMjA0NzczMCwidXNlcl9pZCI6ImRnR2s0Rk9jTVNmNUtiSUJxa1FBdGVKb2xMQjMiLCJzdWIiOiJkZ0drNEZPY01TZjVLYklCcWtRQXRlSm9sTEIzIiwiaWF0IjoxNzM2MTg0MzYxLCJleHAiOjE3MzYxOTg3NjEsImVtYWlsIjoiam1lbGxveUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMzU0MTc1Mjk2MzYyNjY0ODQzMCJdLCJlbWFpbCI6WyJqbWVsbG95QGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.PcdwptzAd3YpjyZkbigqJw5fmsF-Nj64NPp1o3l7gxd2DxH3H2cIxx8H5N5TLxVyKwhiqM3NQcaztl3TD0L2mtW7UzMQAEaP2KvQbyQdAtjgWJY6ii8ecCKXcEW1ua9Y1LgALVkmdQMF1SZXqO5aG-qGt1CPudWiNyCAI3LFPVE0xPGQ_qcG1wMhtadYTNVipZwzf1iDoM1r6H50nMnKhXp575l_bA1w3B-oVuhEJSXoyOe7td3iOryu1VYUFtNWFQI4kBmVlOefyH9ebCzMqzVlGxNEC8q59Jrtp8orzD9pQYaJQ0Q_9Zllqwe-1x0z4a3KEvAIIpFVoI5OhYlU6g; cf_clearance=T24QHEIHiC9i.xyEqUtWGCRh4fFZeitxHrqQJhX3wk8-1736184359-1.2.1.1-B3c4P1I7eaEScl5EwMe284SQtJrgtnG_uYN3OmdTzFRdb9wKoGhXn.dVZa_mgr6FFILS3nRDHFz_kaZnGBXxmtmlhjhfImARMhVEBZFacQqf5erNpicJyJ_N__.qViitwATqYQS1vMXULlwW3ZcwWWDybgc9Q_3RnOzKuQ.t3nphnYoeTYNRqO2721wXBC5dQe0g6UDQhDPkzbutrm2iHorzZV1OAVw9emhJauAR7q65YT1_mfnIfTQyNyFeX0hmUJdWrtL2VodkALGgPzZ3ocPLToOMR0Qkk8L43NlMXlhHFt1j8b7Shs9BDuQjd5TeVd4A_5O6ou_4H8kP8_PYk9WKG0fDuh6M6ZjLBHsQ3d9kCXZ8NRwaiCc34drr4C6iLFRof09pPM0PZpCzKxcjOQ; _iidt=9QCA2hSPRidc3dJyPnGV3S2Ift4fKYs5p4Xn0QvDx37OkWZBln/zBbN/sQdAum3N3rW5m4vPv+Y7vc/g7iqGoR77vP/h7VlfqSSJgfM=; _vid_t=VeEDvLVMkTdAuulPQfoV7aydtNMEXai9iJrjCkDp/fG4Rm6n+uuq/XsbHPqO9Ee4k+1HQy2xZSsOHybywR7MYMchddmV2XHLy4Swtps="

    request = [
        "dgGk4FOcMSf5KbIBqkQAteJolLB3",
        100,
        0,
        {"orderBy": "desc", "prompt": "$undefined", "type": "$undefined"},
    ]

    r = requests.Session()
    r.cookies.update(
        {
            "cookie": cookie,
        }
    )
    r.headers.update(
        {
            "content-type": "text/plain",
            "referer": "https://www.mage.space/u/jmelloy",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
            "accept": "text/x-component",
        }
    )
    url = "https://www.mage.space/u/jmelloy"

    seen = True
    offset = 0
    while seen:
        seen = False
        request[2] = offset
        print(request)
        text, _ = wrap(r, url, data=request)

        potential_json = extract_braces(text)
        for json_str in sorted(potential_json, key=len, reverse=True):
            if seen:
                continue
            try:
                data = json.loads(json_str.replace('\\"', '"'))

                if "uid" in data and "children" in data:
                    images = data["children"][-1]["creations"]
                    logger.info(
                        f"Found {len(images)} images from {images[0]['created_at']} to {images[-1]['created_at']}"
                    )
                    for image in data["children"][-1]["creations"]:
                        image["created_at"] = image["created_at"].replace("$D", "")
                        image["updated_at"] = image["updated_at"].replace("$D", "")
                        yield image
                        seen = True

            except json.JSONDecodeError as e:
                print(json_str, e)

        offset += 100


def main():
    for image in yield_images():
        print(
            image["created_at"],
            image["url"].split("/")[-1],
            image.get("concept_override", {}).get("prompt"),
        )

        filename = os.path.join(
            "output",
            "mage.space",
            "jmelloy",
            image["created_at"].split("T")[0].replace("-", "/"),
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
