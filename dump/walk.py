import sys
import os
from PIL import Image, ImageTk, UnidentifiedImageError
import tkinter as tk
import shutil
import json

def search_metadata(data: dict):
    r = {}
    for k, v in data.items():
        if isinstance(v, dict):
            r.update(search_metadata(v))
        else:
            if k == "prompt":
                r["prompt"] = v
            if k.startswith("created"):
                r["created_at"] = v
    return r

def get_metadata(file):
    data = {}
    if os.path.exists(file + ".json"):
        with open(file + ".json") as f:
            data = json.load(f)
    else:
        folder = os.path.dirname(file)
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        for f in files:
            filename = os.path.basename(f)
            with open(os.path.join(folder, f)) as f:
                content = f.read()
                if filename in content:
                    data = json.loads(content)

    if data:
        return search_metadata(data)

    return None

def get_images(directory):
    supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
    file_response = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(supported_formats):
                metadata = get_metadata(os.path.join(root, file))
                created_at = ''
                prompt = ''
                if metadata:
                    created_at = metadata["created_at"]
                    prompt = metadata["prompt"]
                file_response.append((os.path.join(root, file), created_at, prompt))
                    
    file_response.sort(key=lambda x: x[1])
    prev_prompt = None
    for file, dt, prompt in file_response:
        if prompt != prev_prompt:
            print(dt, prompt)
        yield file
        prev_prompt = prompt


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
            img = img.resize((800, 800))
            root.title(f"Image Viewer - {os.path.basename(image)}")

            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo

            def on_yes():
                print(image)
                shutil.copy(image, dest_dir)
                update_shown_images(image)
                show_next_image()

            def on_no():
                update_shown_images(image)
                show_next_image()

            yes_button.config(command=on_yes)
            no_button.config(command=on_no)
        except UnidentifiedImageError:
            update_shown_images(image)
            show_next_image()
        except StopIteration:
            root.quit()

    image = next(image_iter)
    img = Image.open(image)
    img = img.resize((800, 800))
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()

    yes_button = tk.Button(root, text="Yes")
    yes_button.pack(side=tk.LEFT, padx=10, pady=10)

    def on_no():
        update_shown_images(image)
        show_next_image()

    no_button = tk.Button(root, text="No")
    no_button.pack(side=tk.RIGHT, padx=10, pady=10)
    no_button.config(command=on_no)

    def on_yes():
        shutil.copy(image, dest_dir)
        update_shown_images(image)
        show_next_image()

    yes_button.config(command=on_yes)

    root.bind("<Left>", lambda event: yes_button.invoke())
    root.bind("<Right>", lambda event: no_button.invoke())

    show_next_image()
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], os.path.join(sys.argv[1], ".log.txt"))
import sys
import os
from PIL import Image, ImageTk, UnidentifiedImageError
import tkinter as tk
import shutil
import json


def get_images(directory):
    supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
    for root, dirs, files in os.walk(directory):
        if dirs:
            print(f"Scanning {root} - {len(dirs)} files")
            file_response = []
            for d in dirs:
                for file in os.listdir(os.path.join(root, d)):
                    if file.lower().endswith(supported_formats):
                        if os.path.exists(os.path.join(root, d, "meta.json")):
                            with open(os.path.join(root, d, "meta.json")) as f:
                                meta = json.load(f)
                                created_at = meta.get(
                                    "createdAt", meta.get("created_at")
                                )
                                if not created_at:
                                    created_at = os.path.getctime(
                                        os.path.join(root, d, file)
                                    )
                                prompt = meta.get("generation", {}).get("prompt")
                                if not prompt:
                                    prompt = meta.get("concept_overrides", {}).get(
                                        "prompt"
                                    )

                            file_response.append(
                                (os.path.join(root, d, file), created_at, prompt)
                            )

            file_response.sort(key=lambda x: x[1])
            prev_prompt = None
            for file, dt, prompt in file_response:
                if prompt != prev_prompt:
                    print(dt, prompt)
                yield file
                prev_prompt = prompt


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
            img = img.resize((800, 800))
            root.title(f"Image Viewer - {os.path.basename(image)}")

            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo

            def on_yes():
                shutil.copy(image, dest_dir)
                update_shown_images(image)
                show_next_image()

            def on_no():
                update_shown_images(image)
                show_next_image()

            yes_button.config(command=on_yes)
            no_button.config(command=on_no)
        except UnidentifiedImageError:
            update_shown_images(image)
            show_next_image()
        except StopIteration:
            root.quit()

    image = next(image_iter)
    img = Image.open(image)
    img = img.resize((800, 800))
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(root, image=photo)
    label.pack()

    yes_button = tk.Button(root, text="Yes")
    yes_button.pack(side=tk.LEFT, padx=10, pady=10)

    def on_no():
        update_shown_images(image)
        show_next_image()

    no_button = tk.Button(root, text="No")
    no_button.pack(side=tk.RIGHT, padx=10, pady=10)
    no_button.config(command=on_no)

    def on_yes():
        shutil.copy(image, dest_dir)
        update_shown_images(image)
        show_next_image()

    yes_button.config(command=on_yes)

    root.bind("<Left>", lambda event: no_button.invoke())
    root.bind("<Right>", lambda event: yes_button.invoke())

    show_next_image()
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], os.path.join(sys.argv[1], ".log.txt"))
