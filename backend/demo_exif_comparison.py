#!/usr/bin/env python
"""
Demo script to compare EXIF data from iCloud and macOS fixtures.

This script demonstrates:
1. Loading sample data from both formats
2. Parsing and normalizing EXIF data
3. Pretty printing the EXIF information
4. Comparing data between formats
"""

import json
from pathlib import Path
from app.exif_utils import (
    parse_exif,
    pretty_print_exif,
    compare_exif_data,
    group_exif_data,
)


def main():
    """Main demo function"""
    # Load fixtures
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    
    print("=" * 80)
    print("EXIF Data Comparison Demo - iCloud vs macOS Formats")
    print("=" * 80)
    
    with open(fixtures_dir / "icloud_sample.json", "r") as f:
        icloud_samples = json.load(f)
    
    with open(fixtures_dir / "macos_sample.json", "r") as f:
        macos_samples = json.load(f)
    
    print(f"\nLoaded {len(icloud_samples)} iCloud samples")
    print(f"Loaded {len(macos_samples)} macOS samples")
    
    # Parse first sample from each format
    print("\n" + "=" * 80)
    print("Sample 1: iCloud Format")
    print("=" * 80)
    
    icloud_exif = parse_exif(icloud_samples[0], format_hint="icloud")
    print(pretty_print_exif(icloud_exif))
    
    print("\n" + "=" * 80)
    print("Sample 1: macOS Format")
    print("=" * 80)
    
    macos_exif = parse_exif(macos_samples[0], format_hint="macos")
    print(pretty_print_exif(macos_exif))
    
    # Show grouped data
    print("\n" + "=" * 80)
    print("Grouped Data Example (macOS)")
    print("=" * 80)
    
    grouped = group_exif_data(macos_exif)
    for category, fields in grouped.items():
        non_null_fields = {k: v for k, v in fields.items() if v is not None}
        if non_null_fields:
            print(f"\n{category}:")
            for field, value in non_null_fields.items():
                print(f"  {field}: {value}")
    
    # Compare the two formats
    print("\n" + "=" * 80)
    print("Comparison: iCloud vs macOS")
    print("=" * 80)
    print("\nNote: These are different photos, so comparison shows format differences.")
    print("For the same photo, more fields would match.\n")
    
    comparison = compare_exif_data(icloud_exif, macos_exif)
    
    # Show matching fields
    matches = {k: v for k, v in comparison.items() if v.get("match")}
    if matches:
        print("\nMatching Fields:")
        for field, info in matches.items():
            print(f"  {field}: {info['value']}")
    
    # Show differing fields
    diffs = {k: v for k, v in comparison.items() if not v.get("match")}
    if diffs:
        print("\nDiffering Fields:")
        for field, info in diffs.items():
            print(f"  {field}:")
            print(f"    iCloud: {info['source1']}")
            print(f"    macOS:  {info['source2']}")
    
    # Show statistics
    print("\n" + "=" * 80)
    print("Statistics")
    print("=" * 80)
    
    print(f"\nTotal fields compared: {len(comparison)}")
    print(f"Matching fields: {len(matches)}")
    print(f"Differing fields: {len(diffs)}")
    
    # Test auto-detection
    print("\n" + "=" * 80)
    print("Auto-Detection Test")
    print("=" * 80)
    
    auto_icloud = parse_exif(icloud_samples[0])
    auto_macos = parse_exif(macos_samples[0])
    
    print(f"\niCloud sample auto-detected as: {auto_icloud.raw_data.get('source')}")
    print(f"macOS sample auto-detected as: {auto_macos.raw_data.get('source')}")
    
    # Parse all samples to verify consistency
    print("\n" + "=" * 80)
    print("Parsing All Samples")
    print("=" * 80)
    
    print("\nParsing all iCloud samples...")
    icloud_success = 0
    for i, sample in enumerate(icloud_samples):
        try:
            parse_exif(sample, format_hint="icloud")
            icloud_success += 1
        except Exception as e:
            print(f"  Error parsing iCloud sample {i}: {e}")
    
    print(f"Successfully parsed {icloud_success}/{len(icloud_samples)} iCloud samples")
    
    print("\nParsing all macOS samples...")
    macos_success = 0
    for i, sample in enumerate(macos_samples):
        try:
            parse_exif(sample, format_hint="macos")
            macos_success += 1
        except Exception as e:
            print(f"  Error parsing macOS sample {i}: {e}")
    
    print(f"Successfully parsed {macos_success}/{len(macos_samples)} macOS samples")
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    
    print("\nKey takeaways:")
    print("1. Both formats can be parsed into a common ExifData structure")
    print("2. macOS format has richer camera/EXIF data (ISO, aperture, etc.)")
    print("3. iCloud format has more detailed location accuracy data")
    print("4. Auto-detection works reliably for both formats")
    print("5. Pretty printing makes EXIF data human-readable")


if __name__ == "__main__":
    main()
