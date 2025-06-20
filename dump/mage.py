import requests
import logging
import json
import os
import datetime
from json import JSONEncoder
import re
import gzip
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
            data=data,
        )

    end = datetime.datetime.now()

    logger.info(f""" --> {resp.status_code} - {end - start}""")

    # logger.debug(resp.text)

    if resp.status_code > 205:
        logger.warning(resp.text)

    return resp.content, resp
    


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
    cookie = "ph_phc_lBVvvz084lS4XFbPqGf38TGEa6HnGhmgVHcf4f0NNuX_posthog=%7B%22distinct_id%22%3A%22dgGk4FOcMSf5KbIBqkQAteJolLB3%22%2C%22%24sesid%22%3A%5B1741642694000%2C%22019581fd-98b7-7fda-a4d0-547ed132a3bb%22%2C1741642635447%5D%2C%22%24epp%22%3Atrue%7D; __session=eyJhbGciOiJSUzI1NiIsImtpZCI6IlFEZ1JhQSJ9.eyJpc3MiOiJodHRwczovL3Nlc3Npb24uZmlyZWJhc2UuZ29vZ2xlLmNvbS9tYWdlZG90c3BhY2UiLCJuYW1lIjoiSmVmZnJleSBNZWxsb3kiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSkV1TjNHamtHRWZucG9zNFlXcVhkdHB6cUxTbi0wb3dZZUpDVmhZSURpbEFcdTAwM2RzOTYtYyIsInN0cmlwZVJvbGUiOiJwcm8iLCJhdWQiOiJtYWdlZG90c3BhY2UiLCJhdXRoX3RpbWUiOjE3Mzk4OTk1NDcsInVzZXJfaWQiOiJkZ0drNEZPY01TZjVLYklCcWtRQXRlSm9sTEIzIiwic3ViIjoiZGdHazRGT2NNU2Y1S2JJQnFrUUF0ZUpvbExCMyIsImlhdCI6MTc0MTY0MjYzNywiZXhwIjoxNzQxNjU3MDM3LCJlbWFpbCI6ImptZWxsb3lAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDM1NDE3NTI5NjM2MjY2NDg0MzAiXSwiZW1haWwiOlsiam1lbGxveUBnbWFpbC5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJnb29nbGUuY29tIn19.lRS7jSu20jHDEXHgo365tRoZzDV0CUGTNY5Yrez1xQP22FZ_uDUT0HgD-KyBh205_tzE0D4X-fuaUbL7LTxb5mFF_QpzlgTPJexOmJXpW5hx8MWiHzKLgH-HTuqljaG3S3qNsb-rdXzsD8Dh-12fXxk6EOaRME8XEBlyFV2LN2VHqaCqJwCObzdfayr04V3STv83et-mmuEKw6kNmBxM6i2cqzGIZXq8nhgQEYw-8sGu7wyFZ7izp8FeCcj1IJqGsk2rErDxV9ivbkN1UgF8rxhN-4_Rw0z6yN6pSe_A2_GlcYcSx-4HPjsMtfsHtygUT6e_xkOhxeY3emurUhsY7Q; cf_clearance=qWeKPd2SnxXWauD4cPf_aiBQ6Xwk5tRxDvWgqbeVSds-1741642635-1.2.1.1-3xtCur8HosX55gRItNUepZAp4yOWKggtBNgEB7lUiDfaFCyizVeQN2qtmwHdo4dJyNHu2uW7JS9rkYJeFKoT679HsoPDKvrPeZ4fz6mWp8rGc2RIEcxMhCLRl2iRCjPAawUeAGRljDKp_S46WklhZdMq57.aoAPish8htPJ8n1lo4e68Pu7lznQMTgYZ8y2zGMs9aFfd5_feN1jzZY80VAcv0n4GaHBSAk5fPKCfzv7KIjBrQ9WF7.bJcS9DwsvAzbKnEBiI_31RQ_Ehvk9RsyqOVoeJt9hAze_99wmm1BNYE1liBy0kn_RjNJrRhfe.Cv_fk19fMDToTWGRRSSEjXqAFNBxCHsmbbc6Ic3e3R0; _iidt=JU+/c/irOfY2QalLMMMN+4IodD5VfEq4VP+/6KYwgAW/Jy29tHaA5huTpwu15tVXoTQ/C8ZUF+zltg==; _vid_t=RPaHoBvynXjy3c/wnHnRw/W6hHS+lhCl1fgE4rQDVoUP/SAwTPhc5x7kncI3HBXDDe9UHPmgybM+iA=="

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

def yeild_from_file():
    file = "mage_raw.txt"
    with open(file) as F:
        r = F.read()
    
    for row in extract_braces(r):
        data = json.loads(row)

        for img in data["creations"]:
            yield img
            
def main():
    seen = set()
    for image in yeild_from_file():
        if image["id"] in seen:
            raise Exception("Already seen")
        seen.add(image["id"])
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

        seen.add(image["id"])


if __name__ == "__main__":
    main()
