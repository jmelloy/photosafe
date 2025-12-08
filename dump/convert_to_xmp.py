#!/usr/bin/env python3

import os
import json
import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def create_xmp_metadata(meta_data):
    """Create XMP metadata from the meta.json data."""
    # Create the root element
    xmpmeta = ET.Element("x:xmpmeta")
    xmpmeta.set("xmlns:x", "adobe:ns:meta/")

    # Create RDF element
    rdf = ET.SubElement(xmpmeta, "rdf:RDF")
    rdf.set("xmlns:rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    # Create Description element
    desc = ET.SubElement(rdf, "rdf:Description")
    desc.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    desc.set("xmlns:tiff", "http://ns.adobe.com/tiff/1.0/")
    desc.set("xmlns:xmp", "http://ns.adobe.com/xap/1.0/")
    desc.set("xmlns:photoshop", "http://ns.adobe.com/photoshop/1.0/")
    desc.set("xmlns:exif", "http://ns.adobe.com/exif/1.0/")

    # Add basic metadata
    if "id" in meta_data:
        ET.SubElement(desc, "dc:identifier").text = meta_data["id"]

    # Handle different date formats
    date_fields = ["created_at", "completed"]
    for date_field in date_fields:
        if date_field in meta_data:
            date_str = meta_data[date_field].replace("$D", "")
            try:
                date_obj = datetime.datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )
                ET.SubElement(desc, "xmp:CreateDate").text = date_obj.isoformat()
                ET.SubElement(desc, "xmp:ModifyDate").text = date_obj.isoformat()
                break
            except ValueError:
                continue

    # Add concept override data if present
    if "concept_override" in meta_data and meta_data["concept_override"]:
        concept = meta_data["concept_override"]
        if "prompt" in concept:
            ET.SubElement(desc, "dc:description").text = concept["prompt"]
        if "negative_prompt" in concept:
            ET.SubElement(desc, "photoshop:Instructions").text = concept[
                "negative_prompt"
            ]

    if "architecture_config" in meta_data and meta_data["architecture_config"]:
        concept = meta_data["architecture_config"]
        if "prompt" in concept:
            ET.SubElement(desc, "dc:description").text = concept["prompt"]
        if "negative_prompt" in concept:
            ET.SubElement(desc, "photoshop:Instructions").text = concept[
                "negative_prompt"
            ]

    if "prompt" in meta_data:
        ET.SubElement(desc, "dc:description").text = meta_data["prompt"]

    # Add URL if present
    if "url" in meta_data:
        ET.SubElement(desc, "dc:source").text = meta_data["url"]

    # Add type information
    if "type" in meta_data:
        ET.SubElement(desc, "dc:type").text = meta_data["type"]

    # Add visibility information
    if "visibility" in meta_data:
        ET.SubElement(desc, "xmp:Visibility").text = meta_data["visibility"]

    # Add image dimensions if present
    if "width" in meta_data and "height" in meta_data:
        ET.SubElement(desc, "tiff:ImageWidth").text = str(meta_data["width"])
        ET.SubElement(desc, "tiff:ImageLength").text = str(meta_data["height"])

    # Add workflow information if present
    if "workflowId" in meta_data:
        ET.SubElement(desc, "xmp:WorkflowId").text = meta_data["workflowId"]

    # Add seed information if present
    if "seed" in meta_data:
        ET.SubElement(desc, "xmp:Seed").text = str(meta_data["seed"])

    return prettify(xmpmeta)


def process_json_file(json_path, base_name):
    """Process a JSON file and create corresponding XMP file."""
    try:
        with open(json_path, "r") as f:
            meta_data = json.load(f)

        # Create XMP content
        xmp_content = create_xmp_metadata(meta_data)

        # Create XMP file path
        xmp_path = os.path.join(os.path.dirname(json_path), base_name + ".xmp")

        # Write XMP file
        with open(xmp_path, "w") as f:
            f.write(xmp_content)

        print(f"Created XMP file: {xmp_path}")

    except Exception as e:
        print(f"Error processing {json_path}: {str(e)}")


def main():
    """Main function to process all JSON files in the dump directory."""
    dump_dir = Path("dump")

    # Walk through all directories
    for root, dirs, files in os.walk(dump_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                # Get base name without .json extension
                base_name = os.path.splitext(file)[0]
                # If it's a .jpeg.json file, remove the .jpeg part
                if base_name.endswith(".jpeg"):
                    base_name = base_name[:-5]
                process_json_file(json_path, base_name)


if __name__ == "__main__":
    main()
