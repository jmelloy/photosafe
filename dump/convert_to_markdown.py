#!/usr/bin/env python3

import logging
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
from lib import ImageRouter
from lib.obsidian import copy_to_obsidian
from tqdm import tqdm

logger = logging.getLogger(__name__)

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
    - the curly haired blonde is "heather"
    - Some may contain one character cosplaying as another character, mention both
    
    Return only a JSON array of character names and tags found, like: ["name1", "name2", "tag1", "tag2"]. Don't include the justification.
    
    If no names found, return empty array: []
    """

    if s:
        system_prompt = s

    # Prepare the request payload
    payload = {
        "model": "gemma3:4b",
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
        print(response)
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
            filtered_names.append(camelCase(clean_name))

    return filtered_names


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


def is_image(file):
    file = file.lower()
    return (
        file.endswith(".jpg")
        or file.endswith(".jpeg")
        or file.endswith(".png")
        or file.endswith(".webp")
        or file.endswith(".mp4")
    )


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


tags = {}


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    """Main function to process all JSON files in the dump directory."""
    if len(sys.argv) > 1:
        dump_dir = Path(sys.argv[1])
    else:
        dump_dir = Path("./")

    im = ImageRouter()
    images = []
    for root, dirs, files in os.walk(dump_dir):
        for f in files:
            if is_image(f):
                image_path = Path(root) / f
                images.append(image_path)

    totals = {}
    folder = None
    for image_path in tqdm(sorted(images), desc="Processing images"):
        folder = image_path.parts[0:3]
        if folder != image_path.parts[0:3]:
            folder = image_path.parts[0:3]
            tqdm.write(f"{folder}")

        ImageProcessor = im.get_image_processor(image_path)
        if ImageProcessor:
            image, generation = ImageProcessor.extract_image_metadata(image_path)
            if prompt := generation.get("prompt"):
                if prompt not in tags:
                    tags[prompt] = extract_character_names_from_prompt(prompt)
                    tqdm.write(f"new tags: {prompt[0:40]} {tags[prompt]}")
                image["tags"] = list(set(image.get("tags", []) + tags[prompt]))
            copy_to_obsidian(generation, image, image_path)
            totals[ImageProcessor.__class__.__name__] = (
                totals.get(ImageProcessor.__class__.__name__, 0) + 1
            )

    print(totals)


if __name__ == "__main__":
    main()
