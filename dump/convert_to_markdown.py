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


def query_ollama_for_character_names(prompt_text):
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

    Any lab coat and most brunettes are "sara". 
    Anything involving yoga or fitness is "bri".
    Any man involving photography is "stephen".
    Any nerdy woman is "cady". 
    Any redhead is "michelle"
    The college superhero is "elsie"

    Also include tags for basic themes.
    
    Return only a JSON array of character names and tags found, like: ["name1", "name2", "tag1", "tag2"]. Don't include the justification.
    
    If no names found, return empty array: []
    """

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


def create_markdown_content(metadata, images=[]):
    """Create Markdown content from the meta.json data."""
    # Start with frontmatter

    val = {}
    for k in ["id", "created", "prompt", "url", "source", "tags", "cover"]:
        if k in metadata:
            val[k] = metadata[k]

    for k, v in sorted(metadata.items()):
        if v is not None and v != "":
            val[k] = v

    frontmatter_lines = ["---"]
    fm = yaml.dump(val, sort_keys=False)
    frontmatter_lines.append(fm)
    frontmatter_lines.append("---\n")

    for image in images:
        # Add image link
        frontmatter_lines.append(f"![[{os.path.basename(image)}]]")

    # Combine frontmatter and image link
    markdown_content = "\n".join(frontmatter_lines) + "\n"

    return markdown_content


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
    metadata["source"] = "civitai"
    if "steps" in metadata:
        steps = metadata.pop("steps")
        for step in steps:
            if "params" in step:
                params = step.pop("params")
                for key, value in params.items():
                    if value is not None and value != "":
                        metadata[key] = value

    for k in ["draft", "status", "totalCost", "workflow", "nsfw"]:
        if k in metadata:
            metadata.pop(k)

    return metadata


def process_mage_space(metadata):
    metadata = copy.deepcopy(metadata)
    metadata["source"] = "mage.space"

    concept_override = metadata.pop("concept_override", None)
    if concept_override:
        metadata.update(concept_override)

    architecture_config = metadata.pop("architecture_config", None)
    if architecture_config:
        metadata.update(architecture_config)

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

    if "generation" in metadata:
        generation = metadata.pop("generation")
        for key, value in generation.items():
            if value is not None and value != "":
                metadata[key] = value

    for k in [
        "__typename",
        "collection_images",
        "generated_image_variation_generics",
        "generation_controlnets",
        "generation_elements",
    ]:
        if k in metadata:
            metadata.pop(k)

    return metadata


def process_invoke(metadata):
    metadata["source"] = "invoke"

    if "metadata" in metadata:
        if type(metadata["metadata"]) == str:
            data = json.loads(metadata["metadata"])
            if "positive_prompt" in data and "prompt" not in metadata:
                metadata["prompt"] = data["positive_prompt"]
            if "negative_prompt" in data:
                metadata["negative_prompt"] = data["negative_prompt"]

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

    return metadata


def process_json_file(json_path, images=[], input_meta_data=None):
    """Process a JSON file and create corresponding Markdown file."""

    if input_meta_data is None:
        with open(json_path, "r") as f:
            data = json.load(f)
    else:
        data = input_meta_data

    for k in ["created_at", "createdAt", "created"]:
        if k in data:
            data["created"] = convert_date(data.pop(k))
            break

    for k in ["updated_at", "updatedAt", "updated"]:
        if k in data:
            data["updated"] = convert_date(data.pop(k))
            break

    if "mage.space" in json_path:
        data = process_mage_space(data)
    elif "leonardo" in json_path:
        data = process_leonardo(data)
    elif "generations" in json_path:
        data = process_civitai(data)
    elif "invoke" in json_path:
        data = process_invoke(data)

    if len(images) == 1:
        base_name = os.path.basename(images[0])
    elif "id" in data:
        base_name = data["id"]
    elif "image_name" in data:
        base_name = data["image_name"]
        data["id"] = base_name
    else:
        base_name = os.path.split(json_path)[0].split("/")[-1]
    if images:
        data["cover"] = f"![[{os.path.basename(images[0])}]]"

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
        print("missing prompt", json_path, data)

    data["tags"] = list(set(tags))
    # Create Markdown content
    markdown_content = create_markdown_content(data, images)

    fn = []
    if prompt := data.get("prompt"):
        prompt = re.sub(r"(score[_ ]\d+([ _]up)?, *)+", "", prompt)
        for word in prompt.split(" "):
            fn.append(word)
            if len(" ".join(fn)) > 128:
                fn.append("...")
                break

    id = data.get("id")

    if id:
        id = id.split("-")[0]
        fn.append("-")
        fn.append(id)

    base_name = re.sub(r"[^a-zA-Z0-9 (),-.']+", "-", " ".join(fn)).strip()
    base_name = re.sub(r" +", " ", base_name).strip()

    # Create Markdown file path
    md_path = os.path.join(os.path.dirname(json_path), base_name + ".md")

    # Write Markdown file
    with open(md_path, "w") as f:
        f.write(markdown_content)

    print(f" . {base_name}.md {tags=}")

    return md_path, data


def is_image(file):
    file = file.lower()
    return file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png")


seen = set()


def copy_images(metadata, md_path, images):
    date_str = datetime.datetime.fromisoformat(metadata["created"])
    date_format = "%Y/%m %b/W%V/%d (%A)"
    path = os.path.join(
        "/Users/jeffreymelloy/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/AI",
        date_str.strftime(date_format),
    )
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, "_images"), exist_ok=True)

    if path not in seen:
        seen.add(path)
        files = os.listdir(path)
        for file in files:
            if file.endswith(".md"):
                os.remove(os.path.join(path, file))

    shutil.copy(md_path, path)

    for image in images:
        if not os.path.exists(image):
            shutil.copy(image, os.path.join(path, "_images", os.path.basename(image)))


def main():
    """Main function to process all JSON files in the dump directory."""
    if len(sys.argv) > 1:
        dump_dir = Path(sys.argv[1])
    else:
        dump_dir = Path("./")

    checked = set()

    generations = defaultdict(list)
    invoke_generations = defaultdict(list)

    for root, dirs, files in os.walk(dump_dir):
        base = os.path.dirname(root)
        if base not in checked:
            print(f"{base}")
            checked.add(base)

        if "invoke" in root:
            for f in files:
                if f.endswith(".json"):
                    json_path = os.path.join(root, f)
                    with open(json_path, "r") as f:
                        meta_data = json.load(f)

                    if "metadata" in meta_data:
                        data = json.loads(meta_data["metadata"])
                        del data["seed"]
                        key = json.dumps(data, sort_keys=True)
                        invoke_generations[key].append((root, meta_data))
                        continue
                    else:
                        images = [os.path.join(root, f.replace(".json", ""))]
                        md_path, meta_data = process_json_file(json_path, images)
                        copy_images(meta_data, md_path, images)

        if "leonardo" in root:
            if "meta.json" in files:
                json_path = os.path.join(root, "meta.json")
                with open(json_path, "r") as f:
                    meta_data = json.load(f)

                if "generation" in meta_data:
                    generations[meta_data["generation"]["id"]].append(root)
            continue

        images = []
        meta_data = None

        if "meta.json" in files:
            json_path = os.path.join(root, "meta.json")
            images = [os.path.join(root, file) for file in files if is_image(file)]
            md_path, meta_data = process_json_file(json_path, images)
            copy_images(meta_data, md_path, images)

        if "metadata.json" in files:
            json_path = os.path.join(root, "metadata.json")
            images = []
            for dir in dirs:
                files = os.listdir(os.path.join(root, dir))
                images.extend(
                    [os.path.join(root, dir, file) for file in files if is_image(file)]
                )
            if images:
                md_path, meta_data = process_json_file(json_path, images)
                copy_images(meta_data, md_path, images)

    prev = {}
    for md in sorted(invoke_generations):

        metadata = json.loads(md)
        data = {}
        data["id"] = hashlib.sha256(md.encode()).hexdigest()[:8]
        data["prompt"] = metadata["positive_prompt"]
        data["negative_prompt"] = metadata["negative_prompt"]
        data["tags"] = []
        data["metadata"] = md

        if "renaissance" not in metadata["positive_prompt"]:
            continue

        print(
            "invoke md:",
            data["id"],
            data["prompt"],
            len(invoke_generations[md]),
        )

        images = []
        for root, generation in invoke_generations[md]:
            images.append(os.path.join(root, generation["image_name"]))
            data.update(generation)

        md_path, meta_data = process_json_file(root, images, data)
        copy_images(meta_data, md_path, images)

    for generation_id in generations:
        print(generation_id)

        images = []
        for root in generations[generation_id]:
            files = os.listdir(root)
            images.extend([file for file in files if is_image(file)])

        json_path = os.path.join(generations[generation_id][0], "meta.json")

        with open(json_path, "r") as f:
            meta_data = json.load(f)
            meta_data.pop("id")

        if "generation" in meta_data:
            generation = meta_data.pop("generation")
            generation.update(meta_data)

            md_path, meta_data = process_json_file(json_path, images, generation)

            date_str = datetime.datetime.fromisoformat(generation["created"])
            date_format = "%Y/%m %b/W%V/%d (%A)"
            path = os.path.join(
                "/Users/jeffreymelloy/Library/Mobile Documents/iCloud~md~obsidian/Documents/obsidian/AI",
                date_str.strftime(date_format),
            )
            os.makedirs(path, exist_ok=True)
            os.makedirs(os.path.join(path, "_images"), exist_ok=True)

            shutil.copy(md_path, path)
            for root in generations[generation_id]:
                for image in os.listdir(root):
                    if is_image(image):
                        if not os.path.exists(os.path.join(path, "_images", image)):
                            shutil.copy(
                                os.path.join(root, image),
                                os.path.join(path, "_images", image),
                            )


if __name__ == "__main__":
    main()
