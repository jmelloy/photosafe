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
import subprocess
import ulid

# Configuration
obsidian_root = Path(
    "/Users/jeffreymelloy/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/AI"
)
output_dir = Path("./output/comfyui")


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
        json_match = re.search(r"\[.*\]", response_text)
        if json_match:
            character_names = json.loads(json_match.group())
            return character_names
        else:
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
    """Convert date string to ISO format."""
    date_str = str(date_str).replace("$D", "")
    try:
        date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        date_obj = date_obj.replace(microsecond=0)
        return date_obj.isoformat()
    except ValueError:
        return date_str


# 2025:08:15 10:25:40-07:00
def convert_exif_date(date_str):
    """Convert EXIF date string to ISO format."""
    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S%z")


def create_markdown_content(metadata, content):
    """Create Markdown content from the metadata."""
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
    """Convert text to camelCase format."""
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


def find_prompt(prompt):
    ret = {}
    for k, v in prompt.items():
        title = v["class_type"]
        if v.get("_meta"):
            title = v["_meta"].get("title")

        for inp, value in v["inputs"].items():
            if inp == "text":
                ret[title] = value
    return sorted(ret.values(), key=lambda x: len(x), reverse=True)[0]


def clean_prompt(prompt, workflow=None):
    ret = {}
    nodes = {}

    if workflow:
        ret["id"] = workflow.get("id")
        nodes = {
            node["id"]: {k: v for k, v in node.items() if k in ("id", "type", "order")}
            for node in workflow.get("nodes", [])
        }

    for k, v in prompt.items():
        inputs = {}
        for inp, val in list(v["inputs"].items()):
            if inp == "seed":
                ret["seed"] = val
                continue
            if isinstance(val, list) and len(val) == 2 and val[1] == 0:
                inputs[inp] = val[0]
            else:
                inputs[inp] = val
        nodes[int(k)]["inputs"] = inputs

    ret["nodes"] = sorted(nodes.values(), key=lambda x: x["order"])

    return ret


def check_dates(path):
    for file in sorted(path.rglob("*")):
        if file.is_file():
            mtime = os.path.getmtime(file.resolve())
            ctime = os.path.getctime(file.resolve())
            if mtime != ctime:
                print(
                    f"{file} {datetime.datetime.fromtimestamp(mtime)} {datetime.datetime.fromtimestamp(ctime)}"
                )


def get_exif_data(image_path):
    result = subprocess.run(
        ["exiftool", "-j", str(image_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode == 0 and result.stdout.strip():
        data = json.loads(result.stdout)[0]
        for k, v in data.items():
            if isinstance(v, str) and v.startswith("{"):
                data[k] = json.loads(v)
        return data
    return None


def process_comfyui_metadata(image_path):
    """Extract metadata from ComfyUI image using exiftool."""
    metadata = {
        "source": "comfyui",
        "filename": os.path.basename(image_path),
    }

    try:
        # Use exiftool to extract metadata
        exif_data = get_exif_data(image_path)

        if "Prompt" in exif_data:
            prompt = exif_data["Prompt"]
            workflow = exif_data.get("Workflow")
            metadata["Metadata"] = clean_prompt(prompt, workflow)
            if "seed" in metadata["Metadata"]:
                metadata["seed"] = metadata["Metadata"]["seed"]
                del metadata["Metadata"]["seed"]
            metadata["prompt"] = find_prompt(prompt)

        if "FileModifyDate" in exif_data:
            metadata["created"] = convert_exif_date(exif_data["FileModifyDate"])
        else:
            metadata["created"] = datetime.datetime.fromtimestamp(
                os.path.getmtime(image_path)
            )

        metadata["id"] = str(ulid.ULID.from_datetime(metadata["created"]))[0:10]

        # Also check for standard EXIF fields that might contain metadata
        if "ImageDescription" in exif_data and not metadata["prompt"]:
            metadata["prompt"] = exif_data["ImageDescription"]
        elif "Comment" in exif_data and not metadata["prompt"]:
            metadata["prompt"] = exif_data["Comment"]
        elif "UserComment" in exif_data and not metadata["prompt"]:
            metadata["prompt"] = exif_data["UserComment"]

        # Extract character names from prompt
        if prompt := metadata["prompt"]:
            proper_nouns = extract_character_names_from_prompt(prompt)
            if proper_nouns:
                metadata["tags"] = [
                    camelCase(noun)
                    for noun in proper_nouns
                    if noun and "can't" not in noun.lower()
                ]

    except subprocess.TimeoutExpired:
        print(f"Timeout extracting metadata from {image_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running exiftool on {image_path}: {e}")
    except FileNotFoundError:
        print("exiftool not found. Please install exiftool.")
    # except Exception as e:
    #     print(f"Error processing metadata for {image_path}: {e}")

    return metadata


files = {}


def create_folder_name(metadata):
    """Create folder name from metadata."""
    fn = []

    id = metadata.get("id")[0:8]
    if prompt := metadata.get("prompt"):
        # Clean up prompt for folder name
        prompt = re.sub(r"(score[_ ]\d+([ _]up)?, *)+", "", prompt)
        prompt = re.sub(r"^[0-9]+: ", "", prompt)

        for word in prompt.split(" "):
            fn.append(word)
            if len(" ".join(fn)) > 128:
                fn.append("...")
                break

    fn.insert(0, "-")
    hash = hashlib.sha1(json.dumps(metadata.get("Metadata", {})).encode()).hexdigest()
    if hash in files:
        fn.insert(0, files[hash])
    else:
        files[hash] = id
        fn.insert(0, id)

    folder_name = re.sub(
        r"[^a-zA-Z0-9 (),-.']+", "-", " ".join(fn).replace("(", "").replace(")", "")
    ).strip()
    folder_name = re.sub(r" +", " ", folder_name).strip()

    return folder_name


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


def process_comfyui_image(image_path, output_base_dir):
    """Process a single ComfyUI image."""
    print(f"Processing: {image_path}")

    # Extract metadata
    metadata = process_comfyui_metadata(image_path)

    # Create folder name
    generation_name = create_folder_name(metadata)

    # Create date-based path
    date_str = metadata["created"]
    date_format = "%Y/%m %b/W%V/%d (%A)"
    date_path = date_str.strftime(date_format)

    # Create output directory structure
    output_folder = output_base_dir / date_path / generation_name
    output_folder.mkdir(parents=True, exist_ok=True)

    # Copy image to output
    output_image_path = output_folder / os.path.basename(image_path)
    shutil.copy2(image_path, output_image_path)

    # Create metadata.json
    metadata_file = output_folder / f"{os.path.basename(image_path).split('.')[0]}.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    # Copy to Obsidian
    obsidian_folder = obsidian_root / date_path / generation_name
    obsidian_images = obsidian_folder / "_images"
    obsidian_images.mkdir(parents=True, exist_ok=True)

    markdown_content = create_markdown_content(
        {
            k: v
            for k, v in metadata.items()
            if k
            not in (
                "id",
                "filename",
                "seed",
                "created",
            )
        },
        generation_datacard,
    )
    with open(obsidian_folder / f"{generation_name}.md", "w") as f:
        f.write(markdown_content)

    f = obsidian_folder.parent
    while f != obsidian_root:
        if not os.path.exists(f / f"{f.name}.md"):
            with open(f / f"{f.name}.md", "w") as g:
                g.write(folder_datacard)
        f = f.parent

    # Copy image to Obsidian
    obsidian_image_path = obsidian_images / os.path.basename(image_path)
    shutil.copy2(image_path, obsidian_image_path)

    # Create markdown in Obsidian
    obsidian_file = obsidian_folder / f"{metadata['id']}.md"
    data = {
        k: v
        for k, v in metadata.items()
        if k in ("id", "filename", "created", "seed", "tags")
    }
    data["cover"] = f"![[{os.path.basename(image_path)}]]"
    data["type"] = "image"

    obsidian_markdown = create_markdown_content(
        data,
        f"![[{os.path.basename(image_path)}]]",
    )
    with open(obsidian_file, "w") as f:
        f.write(obsidian_markdown)

    print(f"  Created: {output_folder}")
    print(f"  Copied to Obsidian: {obsidian_folder}")

    return metadata


def process_comfyui_folder(input_folder, output_base_dir):
    """Process all images in a folder as ComfyUI images."""
    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"Input folder does not exist: {input_folder}")
        return

    # Find all image files
    image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
    image_files = []

    for file_path in sorted(input_path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)

    print(f"Found {len(image_files)} image files")

    # Process each image
    for image_path in image_files:
        process_comfyui_image(image_path, output_base_dir)

    print(f"Processed {len(image_files)} images")


def main():
    """Main function to process ComfyUI images."""
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
    else:
        input_folder = "./"

    # Create output directory
    output_base_dir = Path(output_dir)
    output_base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing ComfyUI images from: {input_folder}")
    print(f"Output directory: {output_base_dir}")
    print(f"Obsidian root: {obsidian_root}")

    process_comfyui_folder(input_folder, output_base_dir)

    print("Processing complete!")


if __name__ == "__main__":
    main()
