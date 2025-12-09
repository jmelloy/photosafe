#!/usr/bin/env python3
"""
SQLite to XMP Sidecar File Generator for Invoke AI Database

This script reads metadata from an Invoke AI SQLite database and generates XMP sidecar files
for AI-generated images, including generation parameters and prompts.
"""

import sqlite3
import os
import sys
import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import argparse


class XMPGenerator:
    def __init__(self, db_path, output_dir=None):
        self.db_path = db_path
        self.output_dir = output_dir or "."
        self.conn = None

        # XMP namespaces
        self.namespaces = {
            "x": "adobe:ns:meta/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "dc": "http://purl.org/dc/elements/1.1/",
            "xmp": "http://ns.adobe.com/xap/1.0/",
            "exif": "http://ns.adobe.com/exif/1.0/",
            "tiff": "http://ns.adobe.com/tiff/1.0/",
            "photoshop": "http://ns.adobe.com/photoshop/1.0/",
            "invoke": "http://invoke-ai.github.io/InvokeAI/xmp/1.0/",
        }

    def connect_db(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def get_image_metadata(self):
        """
        Retrieve image metadata from database.
        """
        query = """
        SELECT *
        FROM images
        WHERE deleted_at IS NULL
        """

        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error querying database: {e}")
            return []

    def create_xmp_structure(self):
        """Create the basic XMP XML structure"""
        # Root element with namespaces
        root = Element("x:xmpmeta")
        for prefix, uri in self.namespaces.items():
            root.set(f"xmlns:{prefix}", uri)

        # RDF wrapper
        rdf_root = SubElement(root, "rdf:RDF")

        # Description element
        description = SubElement(rdf_root, "rdf:Description")
        description.set("rdf:about", "")

        return root, description

    def parse_metadata_json(self, metadata_str):
        """Parse the JSON metadata string and extract relevant fields"""
        try:
            if not metadata_str:
                return {}
            metadata = json.loads(metadata_str)
            return metadata
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing metadata JSON: {e}")
            return {}

    def add_dublin_core_metadata(self, desc, row_data, parsed_metadata):
        """Add Dublin Core metadata elements"""
        # Use positive prompt as title/description
        positive_prompt = parsed_metadata.get("positive_prompt", "")
        if positive_prompt:
            dc_title = SubElement(desc, "dc:title")
            title_bag = SubElement(dc_title, "rdf:Alt")
            title_li = SubElement(title_bag, "rdf:li")
            title_li.set("xml:lang", "x-default")
            title_li.text = positive_prompt[:100] + (
                "..." if len(positive_prompt) > 100 else ""
            )

            dc_desc = SubElement(desc, "dc:description")
            desc_bag = SubElement(dc_desc, "rdf:Alt")
            desc_li = SubElement(desc_bag, "rdf:li")
            desc_li.set("xml:lang", "x-default")
            desc_li.text = positive_prompt

        # Add AI generation as creator
        dc_creator = SubElement(desc, "dc:creator")
        creator_seq = SubElement(dc_creator, "rdf:Seq")
        creator_li = SubElement(creator_seq, "rdf:li")
        model_name = parsed_metadata.get("model", {}).get("name", "AI Generated")
        creator_li.text = f"Invoke AI - {model_name}"

        # Add keywords based on category and generation mode
        dc_subject = SubElement(desc, "dc:subject")
        subject_bag = SubElement(dc_subject, "rdf:Bag")

        keywords = ["AI Generated", "Invoke AI"]
        if row_data.get("image_category"):
            keywords.append(row_data["image_category"])
        if parsed_metadata.get("generation_mode"):
            keywords.append(parsed_metadata["generation_mode"])

        for keyword in keywords:
            kw_li = SubElement(subject_bag, "rdf:li")
            kw_li.text = keyword

        # Add rights/copyright
        dc_rights = SubElement(desc, "dc:rights")
        rights_bag = SubElement(dc_rights, "rdf:Alt")
        rights_li = SubElement(rights_bag, "rdf:li")
        rights_li.set("xml:lang", "x-default")
        rights_li.text = "AI Generated Content"

    def add_xmp_metadata(self, desc, row_data, parsed_metadata):
        """Add XMP metadata elements"""
        if row_data.get("created_at"):
            desc.set("xmp:CreateDate", row_data["created_at"])

        if row_data.get("updated_at"):
            desc.set("xmp:ModifyDate", row_data["updated_at"])

        # Add rating if starred
        if row_data.get("starred"):
            desc.set("xmp:Rating", "5")

        # Add app version as metadata
        app_version = parsed_metadata.get("app_version", "")
        if app_version:
            desc.set("xmp:CreatorTool", f"Invoke AI {app_version}")

    def add_exif_metadata(self, desc, row_data, parsed_metadata):
        """Add EXIF metadata elements"""
        # Image dimensions
        if row_data.get("width"):
            desc.set("tiff:ImageWidth", str(row_data["width"]))

        if row_data.get("height"):
            desc.set("tiff:ImageLength", str(row_data["height"]))

        # AI model as "camera" info
        model_info = parsed_metadata.get("model", {})
        if model_info.get("name"):
            desc.set("tiff:Make", "Invoke AI")
            desc.set("tiff:Model", model_info["name"])

        # Software
        desc.set("tiff:Software", "Invoke AI")

        # Use seed as a unique identifier
        seed = parsed_metadata.get("seed")
        if seed:
            desc.set("exif:ImageUniqueID", str(seed))

    def add_invoke_ai_metadata(self, desc, row_data, parsed_metadata):
        """Add Invoke AI specific metadata elements"""
        # Generation parameters
        if parsed_metadata.get("generation_mode"):
            desc.set("invoke:GenerationMode", parsed_metadata["generation_mode"])

        if parsed_metadata.get("positive_prompt"):
            desc.set("invoke:PositivePrompt", parsed_metadata["positive_prompt"])

        if parsed_metadata.get("negative_prompt"):
            desc.set("invoke:NegativePrompt", parsed_metadata["negative_prompt"])

        if parsed_metadata.get("seed"):
            desc.set("invoke:Seed", str(parsed_metadata["seed"]))

        if parsed_metadata.get("cfg_scale"):
            desc.set("invoke:CFGScale", str(parsed_metadata["cfg_scale"]))

        if parsed_metadata.get("steps"):
            desc.set("invoke:Steps", str(parsed_metadata["steps"]))

        if parsed_metadata.get("scheduler"):
            desc.set("invoke:Scheduler", parsed_metadata["scheduler"])

        # Model information
        model_info = parsed_metadata.get("model", {})
        if model_info.get("name"):
            desc.set("invoke:ModelName", model_info["name"])
        if model_info.get("base"):
            desc.set("invoke:ModelBase", model_info["base"])
        if model_info.get("hash"):
            desc.set("invoke:ModelHash", model_info["hash"])

        # Database identifiers
        if row_data.get("session_id"):
            desc.set("invoke:SessionID", row_data["session_id"])

        if row_data.get("node_id"):
            desc.set("invoke:NodeID", row_data["node_id"])

        if row_data.get("image_origin"):
            desc.set("invoke:ImageOrigin", row_data["image_origin"])

        if row_data.get("image_category"):
            desc.set("invoke:ImageCategory", row_data["image_category"])

        # Workflow flag
        if row_data.get("has_workflow"):
            desc.set("invoke:HasWorkflow", "true")

    def generate_xmp_content(self, row_data):
        """Generate complete XMP content for a single image"""
        root, description = self.create_xmp_structure()

        # Parse JSON metadata
        parsed_metadata = self.parse_metadata_json(row_data.get("metadata", ""))

        # Add metadata sections
        self.add_dublin_core_metadata(description, row_data, parsed_metadata)
        self.add_xmp_metadata(description, row_data, parsed_metadata)
        self.add_exif_metadata(description, row_data, parsed_metadata)
        self.add_invoke_ai_metadata(description, row_data, parsed_metadata)

        # Convert to pretty-printed XML string
        rough_string = tostring(root, "utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

        # Remove extra blank lines
        lines = pretty_xml.decode("utf-8").split("\n")
        clean_lines = [line for line in lines if line.strip()]

        return "\n".join(clean_lines)

    def write_xmp_file(self, image_name, xmp_content):
        """Write XMP content to sidecar file"""
        # Remove extension and add .xmp
        base_name = os.path.splitext(image_name)[0]
        xmp_filename = f"{base_name}.xmp"
        xmp_path = os.path.join(self.output_dir, xmp_filename)

        try:
            with open(xmp_path, "w", encoding="utf-8") as f:
                f.write(xmp_content)
            return True
        except IOError as e:
            print(f"Error writing XMP file {xmp_path}: {e}")
            return False

    def process_all_images(self):
        """Process all images from database and generate XMP files"""
        if not self.connect_db():
            return False

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        metadata_rows = self.get_image_metadata()
        if not metadata_rows:
            print("No image metadata found in database")
            return False

        success_count = 0
        total_count = len(metadata_rows)

        print(f"Processing {total_count} images...")

        for row in metadata_rows:
            # Convert row to dictionary for easier access
            row_data = dict(row)
            generation_data = self.parse_metadata_json(row_data.get("metadata", "{}"))

            row_data["prompt"] = generation_data.get("positive_prompt", "")
            row_data["model_name"] = generation_data.get("model", {}).get(
                "name", "Unknown Model"
            )

            with open(
                os.path.join(self.output_dir, row_data["image_name"] + ".json"), "w"
            ) as f:
                json.dump(row_data, f, indent=2)

            # Generate XMP content
            # xmp_content = self.generate_xmp_content(row_data)

            # # Write XMP file
            # if self.write_xmp_file(row_data["image_name"], xmp_content):
            success_count += 1
            #     print(f"Generated XMP for: {row_data['image_name']}")
            # else:
            #     print(f"Failed to generate XMP for: {row_data['image_name']}")

        print(f"\nCompleted: {success_count}/{total_count} XMP files generated")

        if self.conn:
            self.conn.close()

        return success_count > 0


def main():
    parser = argparse.ArgumentParser(
        description="Generate XMP sidecar files from SQLite database"
    )
    parser.add_argument("database", help="Path to SQLite database file")
    parser.add_argument(
        "-o",
        "--output",
        default=".",
        help="Output directory for XMP files (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without creating files",
    )

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(args.database):
        print(f"Error: Database file '{args.database}' not found")
        sys.exit(1)

    # Create generator instance
    generator = XMPGenerator(args.database, args.output)

    if args.dry_run:
        print("DRY RUN - No files will be created")
        # You could add a dry run method here

    # Process images
    if generator.process_all_images():
        print("XMP generation completed successfully")
        sys.exit(0)
    else:
        print("XMP generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
