import os
import shutil
from PIL import Image
import sys


def get_images(directory):
    supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_formats):
                yield os.path.join(root, file)


def display_image(image_path):
    img = Image.open(image_path)
    img.show()


def main(source_dir, dest_dir, log_file):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            shown_images = set(f.read().splitlines())
    else:
        shown_images = set()

    images = get_images(source_dir)
    for image in images:
        if image in shown_images:
            continue

        image_path = os.path.join(source_dir, image)
        display_image(image_path)
        response = (
            input(f"Do you want to copy {image} to {dest_dir}? (y/n): ").strip().lower()
        )

        if response == "y":
            shutil.copy(image_path, dest_dir)

        shown_images.add(image)
        with open(log_file, "a") as f:
            f.write(image + "\n")


if __name__ == "__main__":
    source_directory = sys.argv[1]
    destination_directory = sys.argv[2]
    log_file_path = os.path.join(source_directory, "log.txt")
    main(source_directory, destination_directory, log_file_path)
