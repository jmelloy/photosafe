#!/usr/bin/env python3
"""
Manual demonstration of EXIF extraction and meta.json features.

This script creates a test photo with EXIF data and a meta.json file,
then demonstrates the import functionality.
"""

import tempfile
import json
from pathlib import Path
from PIL import Image
from cli.import_commands import extract_exif_data, parse_meta_json

def main():
    print("PhotoSafe Metadata Import Demonstration")
    print("=" * 60)
    
    # Create a temporary directory for our test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # 1. Create a test image with EXIF data
        print("\n1. Creating test image with EXIF data...")
        img_path = tmpdir_path / "test_photo.jpg"
        img = Image.new('RGB', (800, 600), color='blue')
        
        # Add EXIF data
        exif = img.getexif()
        exif[271] = "Canon"  # Make
        exif[272] = "EOS R5"  # Model
        exif[274] = 1  # Orientation
        exif[33437] = (1, 1000)  # FNumber (f/1.0) as tuple
        exif[34855] = 400  # ISO
        
        img.save(img_path, exif=exif)
        print(f"   ✓ Created image at: {img_path}")
        
        # 2. Extract EXIF data
        print("\n2. Extracting EXIF data...")
        exif_data = extract_exif_data(img_path)
        print(f"   ✓ Extracted EXIF data:")
        print(f"     - Camera Make: {exif_data.get('camera_make', 'N/A')}")
        print(f"     - Camera Model: {exif_data.get('camera_model', 'N/A')}")
        print(f"     - ISO: {exif_data.get('iso', 'N/A')}")
        print(f"     - Aperture: {exif_data.get('aperture', 'N/A')}")
        if '_raw' in exif_data:
            print(f"     - Raw EXIF fields: {len(exif_data['_raw'])} fields")
        
        # 3. Create a meta.json file with arbitrary metadata
        print("\n3. Creating meta.json with arbitrary metadata...")
        meta_json_path = tmpdir_path / "meta.json"
        meta_data = {
            "photographer": "John Doe",
            "location_name": "San Francisco",
            "event": "Tech Conference 2024",
            "custom_tags": ["conference", "technology", "networking"],
            "copyright": "© 2024 John Doe Photography",
            "licensing": {
                "type": "Creative Commons",
                "url": "https://creativecommons.org/licenses/by/4.0/"
            }
        }
        with open(meta_json_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
        print(f"   ✓ Created meta.json at: {meta_json_path}")
        
        # 4. Parse meta.json
        print("\n4. Parsing meta.json...")
        parsed_meta = parse_meta_json(meta_json_path)
        print(f"   ✓ Parsed metadata:")
        if 'fields' in parsed_meta:
            print(f"     - Arbitrary fields stored in 'fields' column:")
            for key, value in parsed_meta['fields'].items():
                print(f"       • {key}: {value}")
        else:
            print(f"     - Recognized PhotoSafe fields:")
            for key, value in parsed_meta.items():
                print(f"       • {key}: {value}")
        
        # 5. Create a photo-specific sidecar
        print("\n5. Creating photo-specific JSON sidecar...")
        sidecar_path = img_path.with_suffix('.jpg.json')
        sidecar_data = {
            "title": "Conference Keynote",
            "description": "Opening keynote at the tech conference",
            "keywords": ["keynote", "conference", "presentation"],
            "favorite": True
        }
        with open(sidecar_path, 'w') as f:
            json.dump(sidecar_data, f, indent=2)
        print(f"   ✓ Created sidecar at: {sidecar_path}")
        
        # 6. Demonstrate metadata priority
        print("\n6. Metadata Priority (highest to lowest):")
        print("   1. JSON sidecar (photo-specific)")
        print("      - title, description, keywords from sidecar")
        print("   2. meta.json (directory-wide)")
        print("      - photographer, location_name, event from meta.json")
        print("   3. EXIF data (extracted from image)")
        print("      - camera_make, camera_model, ISO from EXIF")
        
        print("\n7. How this would be stored in the database:")
        print("   Photo model fields:")
        print("     - title: 'Conference Keynote' (from sidecar)")
        print("     - description: 'Opening keynote...' (from sidecar)")
        print("     - keywords: ['keynote', 'conference', ...] (from sidecar)")
        print("     - favorite: True (from sidecar)")
        print("     - exif: {camera_make: 'Canon', ...} (from EXIF)")
        print("     - fields: {photographer: 'John Doe', ...} (from meta.json)")
        
        print("\n" + "=" * 60)
        print("Demonstration Complete!")
        print("\nTo import these photos for real, run:")
        print(f"  photosafe import --username <user> --library-id <id> --folder {tmpdir_path}")
        
        input("\nPress Enter to exit and clean up temporary files...")

if __name__ == "__main__":
    main()
