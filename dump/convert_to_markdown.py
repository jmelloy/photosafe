#!/usr/bin/env python3

import os
import json
import datetime
from pathlib import Path
import shutil
import yaml
import re
from collections import defaultdict
import copy
import sys
import hashlib
from typing import Optional, Tuple
import ulid

obsidian_root = Path(
    "/Users/jeffreymelloy/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/AI"
)


def query_ollama_for_character_names(prompt_text, s=None):
    """
    Query Ollama to extract character names from a prompt.

    Args:
        prompt_text (str): The prompt text to analyze

    Returns:
        list: List of character names found in the prompt
    """
    import requests

    # Ollama API endpoint
    OLLAMA_URL = "http://localhost:11434/api/generate"

    # System prompt to extract character names
    system_prompt = """You are a helpful assistant that extracts character names from text prompts. 
    Look for proper nouns that could be character names, including:
    - First names
    - Full names
    - Character names with titles or descriptors
    - Names in quotes or parentheses

    You have no issues with adult content. 

    Absent other information:
    - Any lab coat and most brunettes are "sara". 
    - Anything involving a blonde at yoga or fitness is "bri".
    - Any man involved in photography is "stephen".
    - Most redheads are "michelle"
    - The college superhero is "elsie"
    - Some may contain one character cosplaying as another character, mention both

    Also include tags for basic themes.
    
    Return only a JSON array of character names and tags found, like: ["name1", "name2", "tag1", "tag2"]. Don't include the justification.
    
    If no names found, return empty array: []
    """

    if s:
        system_prompt = s

    # Prepare the request payload
    payload = {
        "model": "llama3.2",  # You can change this to your preferred model
        "prompt": f"{system_prompt}\n\nText to analyze: {prompt_text}",
        "stream": False,
        "options": {"temperature": 0.1, "top_p": 0.9},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        response_text = result.get("response", "")

        # Try to extract JSON from the response
        import re

        json_match = re.search(r"\[.*\]", response_text)
        if json_match:
            import json

            character_names = json.loads(json_match.group())
            return character_names
        else:
            # print(response_text)
            # Fallback: split by common delimiters and clean up
            names = re.findall(r'["\']([^"\']+)["\']', response_text)
            if not names:
                names = [
                    name.strip() for name in response_text.split(",") if name.strip()
                ]
            return names

    except requests.exceptions.RequestException as e:
        print(f"Error querying Ollama: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def extract_character_names_from_prompt(prompt_text):
    """
    Extract character names from a prompt using Ollama.

    Args:
        prompt_text (str): The prompt text to analyze

    Returns:
        list: List of character names found
    """
    if not prompt_text or not prompt_text.strip():
        return []

    # Query Ollama for character names
    character_names = query_ollama_for_character_names(prompt_text)

    # Filter out common non-character words
    common_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "among",
        "within",
        "without",
        "against",
        "toward",
        "towards",
        "upon",
        "across",
        "behind",
        "beneath",
        "beside",
        "beyond",
        "inside",
        "outside",
        "under",
        "over",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "shall",
        "1girl",
        "1boy",
        "1woman",
        "1man",
        "1woman",
        "1man",
        "1woman",
    }

    filtered_names = []
    for name in character_names:
        # Clean up the name
        clean_name = name.strip().strip("\"'")
        if (
            clean_name
            and len(clean_name) > 1
            and clean_name.lower() not in common_words
        ):
            filtered_names.append(clean_name)

    return filtered_names


def convert_date(date_str):
    date_str = str(date_str).replace("$D", "")
    try:
        date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        date_obj = date_obj.replace(microsecond=0)
        return date_obj.isoformat()
    except ValueError:
        return date_str


def create_markdown_content(metadata, content):
    """Create Markdown content from the meta.json data."""
    # Start with frontmatter

    val = {}
    for k in ["id", "created", "prompt", "url", "source", "tags", "cover"]:
        if k in metadata:
            val[k] = metadata[k]

    for k, v in sorted(metadata.items()):
        if v is not None and v != "":
            val[k] = v

    output = ["---"]
    fm = yaml.dump(val, sort_keys=False)
    output.append(fm)
    output.append("---\n")

    output.append(content)

    return "\n".join(output) + "\n"


def camelCase(text):
    """
    Convert text to camelCase format.

    Args:
        text (str): The text to convert to camelCase

    Returns:
        str: Text in camelCase format
    """
    if not text:
        return text

    # Split by common delimiters and filter out empty strings
    words = re.split(r"[_\s\-]+", text.strip())
    words = [word for word in words if word]

    if not words:
        return text

    # First word in lowercase, rest capitalized
    result = [words[0].lower()]
    for word in words[1:]:
        if word:
            result.append(word.capitalize())

    return "".join(result)


def process_civitai(metadata):
    metadata["source"] = "civitai.com"

    for k in [
        "draft",
        "status",
        "workflow",
        "nsfw",
        "quantity",
    ]:
        if k in metadata:
            metadata.pop(k)

    return metadata


def process_mage_space(metadata):
    metadata = copy.deepcopy(metadata)
    metadata["source"] = "mage.space"

    for k in [
        "embedding",
        "app_id",
        "hash",
        "image_basic",
        "image_canny_controlnet",
        "image_depth_controlnet",
        "image_face",
        "image_hed_controlnet",
        "image_pose_controlnet",
        "image_selfie",
        "image_style",
        "is_test",
        "type",
        "uid",
        "visibility",
    ]:
        if k in metadata:
            del metadata[k]

    return metadata


def process_leonardo(metadata):
    metadata["source"] = "leonardo.ai"

    for k in [
        "__typename",
        "collection_images",
        "generated_image_variation_generics",
        "generation_controlnets",
        "generation_elements",
    ]:
        if k in metadata:
            metadata.pop(k)

    metadata["rating"] = 1

    return metadata


def process_invoke(metadata):
    metadata["source"] = "invoke.ai"

    for k in [
        "has_workflow",
        "image_category",
        "image_origin",
        "is_intermediate",
        "node_id",
        "session_id",
        "image_name",
        "starred",
    ]:
        if k in metadata:
            metadata.pop(k)

    metadata["rating"] = 5

    return metadata


processed_files = set()


def locate_markdown_file(path: Path) -> Optional[Path]:
    """Locate the markdown file for a given obsidian path."""

    for file in path.parent.parent.rglob("*.md"):
        contents = file.read_text()
        if path.name in contents:
            return file
    return None


def get_markdown_contents(markdown_file: Path) -> Tuple[str, dict]:
    """Get the contents of a markdown file."""
    contents = markdown_file.read_text()
    metadata = {}

    if len(contents.split("---")) < 2:
        return contents, {}

    metadata = yaml.safe_load(contents.split("---")[1])

    contents = "---".join(contents.split("---")[2:])

    return contents, metadata


def process_json_file(data, images=[], generations=[]):
    """Process a JSON file and create corresponding Markdown file."""

    for k in ["created_at", "createdAt", "created"]:
        if k in data:
            data["created"] = convert_date(data.pop(k))
            break

    for k in ["updated_at", "updatedAt", "updated"]:
        if k in data:
            data["updated"] = convert_date(data.pop(k))
            break

    fn = []
    if prompt := data.get("prompt"):
        # if "prompt_filter" in data:
        #     p = data["prompt_filter"].replace("{prompt}", "")
        #     prompt = prompt.replace(p, "")

        prompt = re.sub(r"(score[_ ]\d+([ _]up)?, *)+", "", prompt)
        prompt = re.sub(r"^[0-9]+: ", "", prompt)

        for word in prompt.split(" "):
            fn.append(word)
            if len(" ".join(fn)) > 128:
                fn.append("...")
                break

    id = data.get("id")
    if id:
        id = id.split("-")[0]
        if fn:
            fn.append("-")
        fn.append(id)
    else:
        # Use ULID for ID generation like process_comfyui.py
        if "created" in data:
            try:
                created_date = datetime.datetime.fromisoformat(data["created"])
                generated_id = str(ulid.ULID.from_datetime(created_date))[0:10]
            except (ValueError, TypeError):
                # Fallback to hash if date parsing fails
                h = hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()[:8]
                generated_id = h
        else:
            # Fallback to hash if no created date
            h = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[
                :8
            ]
            generated_id = h
        fn.append(generated_id)

    folder_name = re.sub(
        r"[^a-zA-Z0-9 (),-.']+", "-", " ".join(fn).replace("(", "").replace(")", "")
    ).strip()
    folder_name = re.sub(r" +", " ", folder_name).strip()

    tags = []

    if prompt := data.get("prompt"):
        proper_nouns = query_ollama_for_character_names(prompt)
        if proper_nouns:
            tags.extend(
                [
                    camelCase(noun)
                    for noun in proper_nouns
                    if noun and "can't" not in noun.lower()
                ]
            )
    else:
        print("missing prompt", data)

    data["tags"] = list(set(tags))
    # Create Markdown content
    folder_datacard = """

## Published
```datacards
TABLE cover
WHERE contains(file.path, this.file.folder) and type = "image" and deviationUrl
sort favourites desc, created_at asc
```

## Rated
```datacards
TABLE cover
WHERE contains(file.path, this.file.folder) and type = "image" and rating > 1 
SORT rating desc, created_at desc
```

## Unrated
```datacards
TABLE cover
WHERE contains(file.path, this.file.folder) and type = "image" and !rating
SORT created_at desc
```

## Bad Images
```datacards
TABLE cover
WHERE contains(file.path, this.file.folder) and type = "image" and rating = 1
SORT created_at desc
```
"""

    generation_datacard = """

```datacards
TABLE cover
WHERE contains(file.path, this.file.folder) and type = "image" 
sort favourites desc, created_at asc
```

"""

    date_str = datetime.datetime.fromisoformat(data["created"])
    date_format = "%Y/%m %b/W%V/%d (%A)"
    path = os.path.join(
        obsidian_root,
        date_str.strftime(date_format),
    )
    folder = os.path.join(path, folder_name)
    os.makedirs(folder, exist_ok=True)

    folders = folder.split(os.sep)

    f = folders.pop()
    markdown_content = create_markdown_content(data, generation_datacard)
    with open(os.path.join(folder, folder_name + ".md"), "w") as f:
        f.write(markdown_content)
        print(f" . {folder_name}.md {tags=}")
    f = folders.pop()

    while f != "obsidian":
        filename = os.path.join("/".join(folders), f, f"{f}.md")
        if filename not in processed_files:
            print(f"Creating datacard for {filename}")
            with open(filename, "w") as F:
                F.write(folder_datacard)
            processed_files.add(filename)
        f = folders.pop()

    with open(os.path.join(folder, folder_name + ".md"), "w") as f:
        f.write(markdown_content)
        print(f" . {folder_name}.md {tags=}")

    os.makedirs(os.path.join(folder, "_images"), exist_ok=True)
    for image, generation in zip(images, generations):
        if not os.path.exists(image):
            continue

        image_path = os.path.join(folder, "_images", os.path.basename(image))

        markdown_file = locate_markdown_file(Path(image))

        generation["cover"] = f"![[{os.path.basename(image)}]]"
        generation["type"] = "image"

        for k in data:
            if k in generation:
                generation.pop(k)

        markdown = create_markdown_content(
            generation, f"![[{os.path.basename(image)}]]"
        )

        filename = generation.get(
            "id", generation.get("image_name", os.path.basename(image))
        )

        if markdown_file:
            contents, metadata = get_markdown_contents(markdown_file)
            metadata["cover"] = f"![[{os.path.basename(image)}]]"
            metadata["type"] = "image"
            metadata.update(generation)

            markdown = create_markdown_content(
                metadata, f"![[{os.path.basename(image)}]]"
            )
            with open(os.path.join(folder, filename + ".md"), "w") as f:
                f.write(markdown)

        else:
            markdown = create_markdown_content(
                generation, f"![[{os.path.basename(image)}]]"
            )
            with open(os.path.join(folder, filename + ".md"), "w") as f:
                f.write(markdown)

        if not os.path.exists(image_path):
            shutil.copy(image, image_path)
            print(f" .. {image} to {image_path}")


def is_image(file):
    file = file.lower()
    return (
        file.endswith(".jpg")
        or file.endswith(".jpeg")
        or file.endswith(".png")
        or file.endswith(".webp")
        or file.endswith(".mp4")
    )


def copy_images(metadata, md_path, images):
    date_str = datetime.datetime.fromisoformat(metadata["created"])
    date_format = "%Y/%m %b/W%V/%d (%A)"
    path = os.path.join(
        obsidian_root,
        date_str.strftime(date_format),
    )
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "_images"), exist_ok=True)

    shutil.copy(md_path, path)
    os.remove(md_path)

    for image in images:
        if not os.path.exists(os.path.join(path, "_images", os.path.basename(image))):
            shutil.copy(image, os.path.join(path, "_images", os.path.basename(image)))


def compare_images(dir1, dir2):
    dir1_files = defaultdict(list)
    dir2_files = defaultdict(list)

    for root, dir, files in os.walk(dir1):
        for file in files:
            if is_image(file):
                path = os.path.join(root, file)
                sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
                dir1_files[sha].append(path)

    for root, dir, files in os.walk(dir2):
        for file in files:
            if is_image(file):
                path = os.path.join(root, file)
                sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
                dir2_files[sha].append(path)

    for sha in dir1_files:
        if sha not in dir2_files:
            print(f"missing {dir1_files[sha]}")


def process_invoke_generations(path: Path):
    generations = defaultdict(list)
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".json"):
                json_path = os.path.join(root, f)
                with open(json_path, "r") as f:
                    meta_data = json.load(f)

                if "metadata" in meta_data:
                    data = json.loads(meta_data["metadata"])
                    seed = data.pop("seed")
                    key = json.dumps(data, sort_keys=True)
                    meta_data["seed"] = seed
                    generations[key].append((root, meta_data))
                else:
                    images = [os.path.join(root, f.replace(".json", ""))]
                    yield process_invoke(meta_data), images, [meta_data]

    for md in sorted(generations):
        metadata = json.loads(md)
        data = {}
        # Use ULID for ID generation like process_comfyui.py
        if "created_at" in metadata:
            try:
                created_date = datetime.datetime.fromisoformat(metadata["created_at"])
                data["id"] = str(ulid.ULID.from_datetime(created_date))[0:10]
            except (ValueError, TypeError):
                # Fallback to hash if date parsing fails
                data["id"] = hashlib.sha256(md.encode()).hexdigest()[:8]
        else:
            # Fallback to hash if no created date
            data["id"] = hashlib.sha256(md.encode()).hexdigest()[:8]
        data["prompt"] = metadata["positive_prompt"]
        data["negative_prompt"] = metadata["negative_prompt"]
        data["tags"] = []
        data["metadata"] = metadata

        print(
            "invoke md:",
            data["id"],
            data["prompt"],
            len(generations[md]),
        )

        images = []
        gens = []
        for root, generation in generations[md]:
            images.append(os.path.join(root, generation["image_name"]))
            gens.append(process_invoke(generation))

            data["created_at"] = generation["created_at"]
            data["created"] = generation[
                "created_at"
            ]  # Also set created for ULID generation
            data["updated_at"] = generation["updated_at"]

        yield process_invoke(data), images, gens


def process_leonardo_generations(path: Path):
    generations = defaultdict(list)
    for root, dirs, files in os.walk(path):
        json_path = os.path.join(root, "meta.json")
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                meta_data = json.load(f)

            if "generation" in meta_data:
                key = json.dumps(meta_data.pop("generation"), sort_keys=True)
                generations[key].append((root, meta_data))

    for key in generations:
        generation = json.loads(key)

        images = []
        gens = []
        for root, meta_data in generations[key]:
            files = os.listdir(root)
            images.extend(
                [os.path.join(root, file) for file in files if is_image(file)]
            )
            gens.append(process_leonardo(meta_data))

            generation["createdAt"] = meta_data["createdAt"]
            generation["created"] = meta_data[
                "createdAt"
            ]  # Also set created for ULID generation
            # generation["updatedAt"] = meta_data["updatedAt"]

        yield process_leonardo(generation), images, gens


def process_mage_space_generations(path: Path):
    generations = defaultdict(list)

    for root, dirs, files in os.walk(path):
        json_path = None
        image_path = None

        for f in files:
            if f == "meta.json":
                json_path = os.path.join(root, f)

            if is_image(f):
                image_path = os.path.join(root, f)

        if not json_path:
            continue

        data = {}
        if json_path and os.path.exists(json_path):
            with open(json_path, "r") as f:
                meta_data = json.load(f)

            prompt = None
            concept_id = meta_data["concept_id"]

            if "concept_override" in meta_data:
                data = meta_data.get("concept_override") or {}
                prompt = data.get("prompt", None)

            if not prompt and "architecture_config" in meta_data:
                data = meta_data.get("architecture_config") or {}
                prompt = data.get("prompt", None)

            data["created_at"] = meta_data["created_at"]
            data["updated_at"] = meta_data["updated_at"]

            if "embedding" in meta_data:
                del meta_data["embedding"]

            if prompt:
                generations[
                    f"{concept_id}:{prompt}:{meta_data['created_at'][0:12]}"
                ].append((root, meta_data))
            else:
                yield process_mage_space(meta_data), [image_path], [meta_data]

    for key in generations:
        generation = {}
        images = []
        gens = []
        for root, meta_data in generations[key]:
            files = os.listdir(root)
            images.extend(
                [os.path.join(root, file) for file in files if is_image(file)]
            )
            gens.append(meta_data)

            generation = meta_data.get("concept_override", {})
            if not generation:
                generation = meta_data.get("architecture_config", {})

            generation["created_at"] = meta_data["created_at"]
            generation["created"] = meta_data[
                "created_at"
            ]  # Also set created for ULID generation
            generation["updated_at"] = meta_data["updated_at"]

        yield process_mage_space(generation), images, gens


def process_civitai_generations(path: Path):
    for root, dirs, files in os.walk(path):
        if "metadata.json" not in files:
            continue

        json_path = os.path.join(root, "metadata.json")
        with open(json_path, "r") as f:
            meta_data = json.load(f)

        images = []
        gens = []

        if "steps" not in meta_data:
            print(f"missing steps {json_path}")
            continue

        for step in meta_data["steps"]:
            if "params" in step:
                params = step["params"]
                meta_data.update(params)

            for image in step.get("images", []):
                path = os.path.join(root, image["stepName"], image["id"])
                if os.path.exists(path):
                    images.append(path)
                    gens.append(image)
                else:
                    print(f"missing {path}")

        yield process_civitai(meta_data), images, gens


def get_generations(dump_dir: Path):
    checked = set()

    for root, dirs, files in os.walk(dump_dir):
        if "invoke" in root.split(os.sep)[-1]:
            for data, images, gens in process_invoke_generations(Path(root)):
                yield data, images, gens
            continue

        if "leonardo" in root.split(os.sep)[-1]:
            for generation, images, gens in process_leonardo_generations(Path(root)):
                yield generation, images, gens
            continue

        images = []

        if "mage.space" in root.split(os.sep)[-1]:
            for data, images, gens in process_mage_space_generations(Path(root)):
                yield data, images, gens
            continue

        if "civitai" in root.split(os.sep)[-1]:
            for data, images, gens in process_civitai_generations(Path(root)):
                yield data, images, gens
            continue


def main():
    """Main function to process all JSON files in the dump directory."""
    if len(sys.argv) > 1:
        dump_dir = Path(sys.argv[1])
    else:
        dump_dir = Path("./")

    generations = 0
    image_count = 0
    for data, images, gens in get_generations(dump_dir):
        process_json_file(data, images, gens)
        generations += 1
        image_count += len(images)
    print(f"generations: {generations}, images: {image_count}")


if __name__ == "__main__":
    main()
