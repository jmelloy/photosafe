#!/usr/bin/env python3
from pathlib import Path
import sys
import logging
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from lib.obsidian import copy_to_obsidian
from lib.invoke import Invoke


def is_image(file):
    return file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg")


def main():
    """Main function to process Mage images."""
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
    else:
        input_folder = "./output/invoke"

    print(f"Processing Invoke images from: {input_folder}")

    input_path = Path(input_folder)

    if not input_path.exists():
        print(f"Input folder does not exist: {input_folder}")
        return

    # Process each image
    total = 0
    invoke = Invoke()
    for root, dirs, files in os.walk(input_path):
        for file in files:
            if is_image(file):
                file_path = Path(root) / file
                image, generation = invoke.extract_image_metadata(file_path)
                copy_to_obsidian(generation, image, file_path)
                total += 1

    print(f"Processed {total} images")
    print("Processing complete!")


if __name__ == "__main__":
    main()
