import sys
import os
from PIL import Image, ImageTk
import tkinter as tk
import shutil


def get_images(directory):
    supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
    for root, dirs, files in os.walk(directory):
        if dirs:
            print(f"Scanning {root} - {len(dirs)} files")
        for file in files:
            if file.lower().endswith(supported_formats):
                yield os.path.join(root, file)


def main(source_dir, dest_dir, log_file):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            shown_images = set(f.read().splitlines())
    else:
        shown_images = set()

    images = get_images(source_dir)

    root = tk.Tk()
    root.title("Image Viewer")
    image_iter = iter(images)

    def update_shown_images(img):
        with open(log_file, "a") as f:
            f.write(img + "\n")
        shown_images.add(img)

    def show_next_image():
        try:
            image = next(image_iter)
            while image in shown_images:
                image = next(image_iter)
            img = Image.open(image)
            img = img.resize((800, 600))
            root.title(f"Image Viewer - {os.path.basename(image)}")

            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo

            def on_yes():
                shutil.copy(image, dest_dir)
                shown_images.add(image)
                update_shown_images(image)
                show_next_image()

            def on_no():
                update_shown_images(image)
                show_next_image()

            yes_button.config(command=on_yes)
            no_button.config(command=on_no)
        except StopIteration:
            root.quit()

    img = Image.open(next(image_iter))
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()

    yes_button = tk.Button(root, text="Yes")
    yes_button.pack(side=tk.LEFT, padx=10, pady=10)

    no_button = tk.Button(root, text="No")
    no_button.pack(side=tk.RIGHT, padx=10, pady=10)

    root.bind("<Left>", lambda event: no_button.invoke())
    root.bind("<Right>", lambda event: yes_button.invoke())

    show_next_image()
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], os.path.join(sys.argv[1], ".log.txt"))
