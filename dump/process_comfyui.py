#!/usr/bin/env python3
from pathlib import Path
import sys
import json
import datetime

from lib.obsidian import copy_to_obsidian
from lib.comfyui import ComfyUI


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def main():
    """Main function to process ComfyUI images."""
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
    else:
        input_folder = "./output/comfyui"

    print(f"Processing ComfyUI images from: {input_folder}")

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

    comfyui = ComfyUI()
    # Process each image
    for image_path in image_files:
        image, generation = comfyui.extract_image_metadata(image_path)
        copy_to_obsidian(generation, image, image_path)
        generation.update(image)
        with open(image_path.with_suffix(".json"), "w") as f:
            json.dump(generation, f, indent=2, cls=DateTimeEncoder)

    print(f"Processed {len(image_files)} images")
    print("Processing complete!")


if __name__ == "__main__":
    main()
