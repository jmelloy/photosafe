import json
import os
import tqdm
import sys
from datetime import datetime


def extract_json(data):
    results = []
    prev = ""
    curly_boi = 0
    in_str = False
    for c in data:
        if c == '"':
            in_str = not in_str

        if c == "{" and not in_str:
            curly_boi += 1

        if curly_boi:
            prev += c
        if c == "}" and not in_str:
            curly_boi -= 1

        if not curly_boi and prev:
            try:
                results.append(json.loads(prev))
            except Exception as E:
                os.makedirs(os.path.join("output", "errors"), exist_ok=True)
                with open(
                    os.path.join("output", "errors", file["uuid"] + ".json"), "w"
                ) as F:
                    F.write(prev)
            prev = ""

    for file in results:
        id = file["cloud_guid"] or file["uuid"]
        dt = datetime.fromisoformat(data["date"])

        folder = os.path.join("output", dt.strftime("%Y/%m/%d"), id)

        filename = os.path.join(folder, "apple.json")

        os.makedirs(folder, exist_ok=True)
        if not os.path.exists(filename):
            with open(filename, "w") as F:
                F.write(json.dumps(file, indent=2))

    return prev


length = os.path.getsize("dump.json")
with open("dump.json") as F:
    data = ""
    for i in tqdm.tqdm(range(0, length, 1024 * 1024)):
        # read in by chunks and build a {} from the json
        chunk = F.read(1024 * 1024)
        data += chunk

        data = extract_json(data)
