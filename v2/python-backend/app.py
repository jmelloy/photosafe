from flask import Flask, request, jsonify
from PIL import Image
from PIL.ExifTags import TAGS
from joycaption import generate_tags, generate_caption
import json
import base64

app = Flask(__name__)


def get_exif_data(image):
    """Extract EXIF data from an image."""
    exif_data = {
        "width": image.width,
        "height": image.height,
        "filename": image.filename.split("/")[-1],
    }
    try:
        exif = image.getexif()
        if exif:
            for tag, value in exif.items():
                decoded_tag = TAGS.get(tag, tag)
                exif_data[decoded_tag] = value
    except Exception as e:
        exif_data["error"] = str(e)

    if "invokeai_metadata" in image.info:
        exif_data["invokeai_metadata"] = json.loads(image.info["invokeai_metadata"])

    return exif_data


@app.route("/thumbnail", methods=["POST"])
def exif():
    if "image" not in request.files:
        return jsonify({"error": "No image file found in the request"}), 400

    file = request.files["image"]
    r = {}
    try:
        image = Image.open(file)
        exif_data = get_exif_data(image)
        r.update(exif_data)
    except Exception as e:
        return jsonify({"error": f"Failed to process the image: {str(e)}"}), 500

    thumbnail = image.copy()
    thumbnail.thumbnail((128, 128))
    base64_thumbnail = base64.b64encode(thumbnail.read())
    r["thumbnail"] = base64_thumbnail.decode("utf-8")

    return jsonify(r)


@app.route("/caption", methods=["POST"])
def caption():
    if "image" not in request.files:
        return jsonify({"error": "No image file found in the request"}), 400

    file = request.files["image"]
    image = Image.open(file)

    caption = generate_caption(image)
    tags = generate_tags(image)

    return jsonify({"caption": caption, "tags": tags})


if __name__ == "__main__":
    app.run(debug=True)
