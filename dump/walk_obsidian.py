import argparse
import os
import re
from pathlib import Path
import shutil
from typing import Dict, Optional, Any
import yaml
import json

#!/usr/bin/env python3
"""
Walk a directory structure and process images with associated metadata.

This script finds images in _images folders, locates their corresponding
markdown files, extracts YAML frontmatter, and prints the mapping with metadata.
"""


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        elif isinstance(o, bytes):
            return o.decode("utf-8", errors="ignore")
        elif isinstance(o, Path):
            return str(o)
        elif hasattr(o, "isoformat"):
            return o.isoformat()
        return super().default(o)


def parse_frontmatter(file_path: Path) -> Dict[str, Any]:
    """
    Parse YAML frontmatter from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Dictionary containing frontmatter data
    """
    if not file_path.exists():
        return {}

    content = file_path.read_text(encoding="utf-8")

    # Match YAML frontmatter between --- delimiters
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}

    try:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}


def truncate_folder_name(folder_name: str, max_length: int = 25) -> str:
    """
    Truncate folder name to max_length on a word boundary.

    Args:
        folder_name: Original folder name
        max_length: Maximum length (default: 25)

    Returns:
        Truncated folder name
    """
    if len(folder_name) <= max_length:
        return folder_name

    truncated = folder_name[:max_length]
    last_space = truncated.rfind(" ")

    if last_space > 0:
        return truncated[:last_space]

    return truncated


def process_image(
    image_path: Path, base_dir: Path, dest: Optional[Path] = None
) -> None:
    """
    Process a single image file and print its metadata.

    Args:
        image_path: Path to the image file
        base_dir: Base directory for relative path calculation
    """
    # Remove _images from path
    parts = list(image_path.relative_to(base_dir).parts)
    new_parts = [p for p in parts if p != "_images" and not re.match(r"W\d\d", p)]
    new_relative_path = Path(*new_parts)

    # Look for {image_name}.md up one folder

    md_file = image_path.parent.parent / f"{image_path.name}.md"
    print(md_file)
    # Extract desired frontmatter fields
    desired_fields = [
        "created",
        "rating",
        "published_time",
        "tags",
        "source",
        "deviationUrl",
        "description",
        "title",
        "galleries",
    ]

    properties = {}
    if md_file.exists():
        frontmatter = parse_frontmatter(md_file)
        properties = {k: frontmatter.get(k) for k in desired_fields if k in frontmatter}

    # Look for parent folder markdown file
    parent_folder = image_path.parent.parent
    parent_md = parent_folder / f"{parent_folder.name}.md"

    if parent_md.exists():
        parent_frontmatter = parse_frontmatter(parent_md)
        if "prompt" in parent_frontmatter:
            properties["prompt"] = parent_frontmatter["prompt"]

    # Truncate folder name
    truncated_folder = truncate_folder_name(parent_folder.name)

    # Print results
    print(f"Old location: {image_path.relative_to(base_dir)}")
    print(f"New location: {new_relative_path}")
    print(f"Folder: {truncated_folder}")
    if properties:
        print("Properties:")
        for key, value in properties.items():
            print(f"  {key}: {value}")
    print()

    if dest:
        os.makedirs(dest / new_relative_path.parent, exist_ok=True)
        if not (dest / new_relative_path).exists():
            shutil.copy2(image_path, dest / new_relative_path)
        metadata = dest / new_relative_path.parent / f".{image_path.name}.json"
        with open(metadata, "w", encoding="utf-8") as f:
            json.dump(
                properties, f, ensure_ascii=False, indent=4, cls=CustomJSONEncoder
            )


def walk_directory(directory: Path, dest: Optional[Path] = None) -> None:
    """
    Walk directory and process all images in _images folders.

    Args:
        directory: Root directory to walk
        dest: Optional destination directory for copying images
    """
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        return

    # Find all images in _images folders
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}

    for image_path in directory.rglob("*"):
        if (
            image_path.is_file()
            and image_path.suffix.lower() in image_extensions
            and "_images" in image_path.parts
        ):
            process_image(image_path, directory, dest)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Walk directory and process images with metadata"
    )
    parser.add_argument("directory", type=Path, help="Directory to walk")
    parser.add_argument(
        "--dest", type=Path, help="Destination directory (not used)", default=None
    )

    args = parser.parse_args()
    walk_directory(args.directory, args.dest)


if __name__ == "__main__":
    main()
