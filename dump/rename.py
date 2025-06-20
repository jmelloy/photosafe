import os
import json
from datetime import datetime

for dir, _, files in os.walk("output"):
    for file in files:
        if file == "apple.json":
            print(os.path.join(dir, file))

            with open(os.path.join(dir, file), "r") as f:
                data = json.loads(f.read())

            id = data["cloud_guid"] or data["uuid"]
            dt = datetime.fromisoformat(data["date"])

            folder = os.path.join("output", dt.strftime("%Y/%m/%d"), id)

            os.makedirs(folder, exist_ok=True)

            for file in os.listdir(dir):
                os.rename(os.path.join(dir, file), os.path.join(folder, file))
            os.rmdir(dir)
