# EXIF Data Parsing and Comparison Utilities

This module provides utilities for parsing, normalizing, and comparing EXIF data from different photo metadata formats, specifically iCloud and macOS Photos formats.

## Overview

The `exif_utils.py` module solves the problem of working with EXIF data from different sources that have incompatible formats. It provides:

- **Parsing**: Extract EXIF data from both iCloud and macOS Photos formats
- **Normalization**: Convert different formats into a common `ExifData` structure
- **Grouping**: Organize EXIF fields by category (Camera, Exposure, Location, etc.)
- **Pretty Printing**: Display EXIF data in human-readable format
- **Comparison**: Compare EXIF data from different sources field-by-field

## Key Components

### ExifData Dataclass

A normalized data structure containing:
- **Camera information**: make, model, lens
- **Exposure settings**: ISO, aperture, shutter speed, focal length, etc.
- **Location data**: latitude, longitude, altitude, accuracy
- **Date/time**: timestamp, timezone offset
- **Image properties**: width, height, orientation
- **Video properties**: duration, fps, bit rate, codec

### Parsing Functions

#### `parse_macos_exif(data: Dict[str, Any]) -> ExifData`
Parses EXIF data from macOS Photos format, which has rich camera settings in the `exif_info` field.

#### `parse_icloud_exif(data: Dict[str, Any]) -> ExifData`
Parses EXIF data from iCloud format, which has detailed location data in the `asset_fields` structure.

#### `parse_exif(data: Dict[str, Any], format_hint: Optional[str] = None) -> ExifData`
Auto-detects the format and parses accordingly. Pass `format_hint="icloud"` or `format_hint="macos"` to force a specific parser.

### Display Functions

#### `group_exif_data(exif: ExifData) -> Dict[str, Dict[str, Any]]`
Groups EXIF fields by category for easier display:
- Camera
- Exposure
- Location
- DateTime
- Image
- Video

#### `pretty_print_exif(exif: ExifData, show_empty: bool = False) -> str`
Creates a human-readable formatted string of EXIF data. Set `show_empty=True` to include fields with None values.

### Comparison Function

#### `compare_exif_data(exif1: ExifData, exif2: ExifData) -> Dict[str, Dict[str, Any]]`
Compares two ExifData objects field-by-field and returns matching and differing fields.

## Usage Examples

### Basic Parsing

```python
from app.exif_utils import parse_exif, pretty_print_exif

# Load your metadata
with open("photo_metadata.json", "r") as f:
    metadata = json.load(f)

# Parse EXIF data (auto-detect format)
exif = parse_exif(metadata)

# Display it
print(pretty_print_exif(exif))
```

### Format-Specific Parsing

```python
from app.exif_utils import parse_macos_exif, parse_icloud_exif

# Parse macOS format
macos_exif = parse_macos_exif(macos_metadata)

# Parse iCloud format
icloud_exif = parse_icloud_exif(icloud_metadata)
```

### Grouping and Display

```python
from app.exif_utils import parse_exif, group_exif_data

exif = parse_exif(metadata)
grouped = group_exif_data(exif)

# Display camera information
camera_info = grouped["Camera"]
for field, value in camera_info.items():
    if value is not None:
        print(f"{field}: {value}")
```

### Comparing Data

```python
from app.exif_utils import parse_exif, compare_exif_data

# Parse two sources
exif1 = parse_exif(metadata1, format_hint="icloud")
exif2 = parse_exif(metadata2, format_hint="macos")

# Compare them
comparison = compare_exif_data(exif1, exif2)

# Show differences
for field, info in comparison.items():
    if not info.get("match"):
        print(f"{field}: {info['source1']} vs {info['source2']}")
```

## Format Differences

### macOS Photos Format
- Structured `exif_info` field with camera settings
- Rich exposure data (ISO, aperture, shutter speed, etc.)
- Camera make, model, and lens information
- Basic location data (latitude, longitude)

### iCloud Format
- Nested structure with `asset_fields` and `fields`
- Detailed location data with accuracy measurements
- Timestamps in milliseconds since epoch
- Orientation and dimension data
- Camera information may be limited or in numeric keys

## Demo Script

Run the demo to see the utilities in action:

```bash
cd backend
python demo_exif_comparison.py
```

This will:
1. Load all fixture samples
2. Parse and display data from both formats
3. Show grouped data by category
4. Compare iCloud vs macOS formats
5. Verify all samples parse successfully

## Testing

Run the comprehensive test suite:

```bash
cd backend
python -m pytest tests/unit/test_exif_utils.py -v
```

Tests cover:
- Parsing both formats (all 25 samples each)
- Auto-detection of formats
- Grouping and pretty printing
- Comparison logic
- Edge cases and error handling

## Data Flow

```
iCloud JSON → parse_icloud_exif() → ExifData
macOS JSON  → parse_macos_exif()  → ExifData
                                       ↓
                            group_exif_data()
                                       ↓
                            pretty_print_exif()
                                       ↓
                          Human-readable output
```

## Notes

- Auto-detection checks for `exif_info` (macOS) or `asset_fields`/`_asset_record` (iCloud)
- All parsers are defensive - missing fields default to `None`
- Raw data is preserved in `ExifData.raw_data` for debugging
- Pretty printing hides empty fields by default
- Comparison only reports fields where at least one source has data

## Future Enhancements

Potential improvements:
- Support for additional EXIF formats (XMP, native EXIF tags)
- More sophisticated iCloud field parsing (numeric keys)
- Coordinate conversion utilities
- Date/time timezone handling improvements
- Video-specific metadata parsing
