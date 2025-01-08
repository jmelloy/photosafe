from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

import os
import tqdm
import json
import random

model_path = "mlx-community/pixtral-12b-8bit"
model, processor = load(model_path)
config = load_config(model_path)

months = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}


def generate_prompt(dir, sample=10):
    people = set()
    places = set()
    images = []

    area = 0

    for d, s, files in os.walk(dir):
        for file in files:
            if file == "apple.json":
                with open(os.path.join(d, file)) as F:
                    data = json.load(F)

                people.update(data.get("persons", []))
                places.update([data.get("place", {}).get("name")])

                if not area:
                    area = data.get("width") * data.get("height")

                if data.get("width") * data.get("height") != area:
                    print(f"Skipping {d} due to different area")
                    continue

                if derivatives := data.get("path_derivatives"):
                    image = None
                    for derivative in derivatives:
                        if "_5005_" in derivative:
                            image = (
                                data.get("score", {}).get("overall"),
                                derivatives[-1],
                            )
                    else:
                        if not image:
                            image = (
                                data.get("score", {}).get("overall"),
                                derivatives[-1],
                            )
                    images.append(image)
    if sample:
        images = sorted(images, key=lambda x: x[0])
        images = [x[1] for x in images[:sample]]

    prompt = f"Write a title and brief overview of these photos. "

    if people:
        prompt += f" These images contain people named {', '.join([p for p in people if p and p != "_UNKNOWN_"])}."

    if places:
        prompt += f" They are taken at: {'; '.join([p for p in places if p])}."

    return prompt, images


if __name__ == "__main__":
    for year in os.listdir("output"):
        for month in os.listdir(f"output/{year}"):
            for day in os.listdir(f"output/{year}/{month}"):
                if os.path.exists("output/{year}/{month}/{day}/moment.yaml"):
                    continue

                prompt, images = generate_prompt(
                    f"output/{year}/{month}/{day}", sample=10
                )
                formatted_prompt = apply_chat_template(
                    processor, config, prompt, num_images=len(images)
                )

                try:
                    output = generate(
                        model,
                        processor,
                        images,
                        formatted_prompt,
                        verbose=False,
                        max_tokens=1000,
                        temperature=0.7,
                    )

                    print(f"{year}/{month}/{day}", output.strip())

                    with open(
                        os.path.join("output", year, month, day, f"moment.yaml"),
                        "w",
                    ) as F:
                        F.write(output.strip())
                except Exception as E:
                    print(f"Error processing {year}/{month}/{day}: {E}")
