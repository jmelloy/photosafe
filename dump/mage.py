import requests
import logging
import json
import os
import datetime
from json import JSONEncoder
import re
import gzip
from convert_to_xmp import create_xmp_metadata

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
    cookie = "ph_phc_lBVvvz084lS4XFbPqGf38TGEa6HnGhmgVHcf4f0NNuX_posthog=%7B%22distinct_id%22%3A%22dgGk4FOcMSf5KbIBqkQAteJolLB3%22%2C%22%24sesid%22%3A%5B1748822103918%2C%2201972de8-9dca-7ac0-a78a-59c37dfc5db9%22%2C1748821908938%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22%24direct%22%2C%22u%22%3A%22https%3A%2F%2Fwww.mage.space%2F%22%7D%7D; __session=eyJhbGciOiJSUzI1NiIsImtpZCI6Ik4yQlkwQSJ9.eyJpc3MiOiJodHRwczovL3Nlc3Npb24uZmlyZWJhc2UuZ29vZ2xlLmNvbS9tYWdlZG90c3BhY2UiLCJuYW1lIjoiSmVmZnJleSBNZWxsb3kiLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSkV1TjNHamtHRWZucG9zNFlXcVhkdHB6cUxTbi0wb3dZZUpDVmhZSURpbEFcdTAwM2RzOTYtYyIsInN0cmlwZVJvbGUiOiJwcm9fcGx1cyIsImF1ZCI6Im1hZ2Vkb3RzcGFjZSIsImF1dGhfdGltZSI6MTc0NzE2NjcwNCwidXNlcl9pZCI6ImRnR2s0Rk9jTVNmNUtiSUJxa1FBdGVKb2xMQjMiLCJzdWIiOiJkZ0drNEZPY01TZjVLYklCcWtRQXRlSm9sTEIzIiwiaWF0IjoxNzQ4ODIyMTAxLCJleHAiOjE3NDg5MDg1MDEsImVtYWlsIjoiam1lbGxveUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJnb29nbGUuY29tIjpbIjEwMzU0MTc1Mjk2MzYyNjY0ODQzMCJdLCJlbWFpbCI6WyJqbWVsbG95QGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6Imdvb2dsZS5jb20ifX0.NR7X8VcLXkYlkz4ltW-yD99rWxinFW9oIOdZZK-kYUxn_y8ScpKuXIqUsn49WGIzacLXGtRUJrBrMdaKg7m3AvOAkA8OV8ljosNb6DDycEnzdp_TMl4-iyf_05QNKxdzCrBMLYJTD7JiiG9KVtIxzVGrYy9DOG3377YEoGvaID3HO8JPQYv7QaROFZVsgAzr01JBKbl7V8Oxp_FeuSzqFyjvAbQ7hIqkto--3Epmn_vpVy9rxJJeIoheP7C-fVIJqNaoaXprxA28JeRgAUxmZdnU3-YQPXbLCaQeB-pkdC4h3RJFzigFDBSkZ0mtiIAZuBN83In9zkGiXVPDM5Te0A; cf_clearance=sdjQDJRnIWpVTwMzq51dlsZydDFgAnTMqUI7Ay9vXkg-1748821909-1.2.1.1-m55SVLynj9WmQBgRlhW0odJ5XVjo_sjdmRsYjgUXyKiq7hLvoI_SMlY4SEUYfcBKni9xCfyZ5zQsA3y_k8YmEDjq8RUErDcV_PaWhtzdmvKcEEj5bivtawse7Q52ZOYs7f7qMGdDlAtynWWhMNLqkqjdxpag61m9zAQF3onO51hj6one_W8HalqVVs5n2yoHJOLTZ2TWB5ejlyR_QLiXFvUKKlkE.pNwZLq3JWcNAUT0qPYmW.s7uOZ2Sc3AF3czLRQFHfocxKK8gUTsZeaNXzGx6O3Tv.Zf3dIMavnkPRmEsWRBB8Sj_k.6a2AV.Lngug2MKDtmEwjVM4MdfkqGWpBKNjHRFX19xyVqYvH055s; _iidt=EU88TS7T3Nqc25zngk6fq+6Dt9ScFjYSsR7cjMB8+GvGi8NY5HFftA4dbq6HOj+/GoKY9EPuSXynSydN0rnBP4GVyKGmPFk3be1vBnk="

    request = ["dgGk4FOcMSf5KbIBqkQAteJolLB3", 100, 0, {
        "orderBy": "desc",
        "prompt": "$undefined",
        "type": "$undefined",
        "tag": "$undefined"
    }]


    session = requests.Session()
    session.cookies.update(
        {
            "cookie": cookie,
        }
    )
    session.headers.update(
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
        text, _ = wrap(session, url, data=json.dumps(request))

        potential_json = extract_braces(text.decode("utf-8"))
        for json_str in sorted(potential_json, key=len, reverse=True):
            if seen:
                continue
            try:
                json_str = re.sub(r'"embedding":\S+\[.*?\],?', '', json_str.replace('\\"', '"')).replace(",}", "}")
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
        if "creations" not in data:
            continue
        for img in data["creations"]:
            if img:
                yield img
            
def main():
    seen = set()
    for image in yeild_from_file():
        if image["id"] in seen:
            continue
            # raise Exception("Already seen")
        seen.add(image["id"])
        prompt = (image.get("concept_override") or {}).get("prompt", "")
        if not prompt:
            prompt = (image.get("architecture_config") or {}).get("prompt", "")

        print(
            image["created_at"],
            image["url"].split("/")[-1],
            prompt
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

        if not os.path.exists(filename):
            with open(filename, "wb") as f:
                f.write(requests.get(image["url"]).content)

        with open(os.path.join(os.path.dirname(filename), "meta.json"), "w") as f:
            f.write(json.dumps(image, indent=2))


        sidecar = create_xmp_metadata(image)
        with open(f"{filename}.xmp", "w") as f:
            f.write(sidecar)

if __name__ == "__main__":
    main()
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
