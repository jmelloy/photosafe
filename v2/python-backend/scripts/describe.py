from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

import os
import tqdm
import json

model_path = "mlx-community/SmolVLM-Instruct-bf16"
model, processor = load(model_path)
config = load_config(model_path)


def parse_output(data):
    idx = data.find("Assistant:")
    if idx == -1:
        return None
    data = data[idx:].replace("Assistant:", "")
    return data.strip()


for dir, subdirs, files in os.walk("output"):
    if subdirs:
        print(dir, len(subdirs))
    else:
        file = "apple.json"
        if os.path.exists(os.path.join(dir, "caption.yaml")):
            continue

        with open(os.path.join(dir, file)) as F:
            data = json.load(F)
            prompt = f"Describe what you see."
            if persons := data.get("persons"):
                prompt += f" It contains people named {', '.join(set(persons))}."

            if name := data.get("place", {}).get("name"):
                prompt += f" It is taken at {name}."

            if "path_derivatives" in data:
                formatted_prompt = apply_chat_template(
                    processor, config, prompt, num_images=1
                )
                images = [data["path_derivatives"][-1]]
                output = generate(
                    model,
                    processor,
                    images,
                    formatted_prompt,
                    verbose=False,
                    max_tokens=1000,
                    temperature=0.7,
                )
                print(dir, output.strip())
                with open(os.path.join(dir, "caption.yaml"), "w") as F:
                    F.write(output.strip())
