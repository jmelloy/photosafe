# Quick Start: EXIF Data Utilities

## 🚀 Quick Start (30 seconds)

### Run the Demo
```bash
cd backend
python demo_exif_comparison.py
```

This will show you:
- ✅ Parsing 50 photo samples (25 iCloud + 25 macOS)
- ✅ Pretty-printed EXIF data
- ✅ Format comparison
- ✅ Auto-detection in action

### Run the Tests
```bash
cd backend
python -m pytest tests/unit/test_exif_utils.py -v
```

Expected result: **36 tests passing in < 1 second**

## 📖 Basic Usage

### Parse Any Format
```python
from app.exif_utils import parse_exif, pretty_print_exif

# Load your metadata (iCloud or macOS format)
import json
with open("photo_metadata.json") as f:
    metadata = json.load(f)

# Parse it (auto-detects format)
exif = parse_exif(metadata)

# Display it beautifully
print(pretty_print_exif(exif))
```

### Compare Two Photos
```python
from app.exif_utils import parse_exif, compare_exif_data

exif1 = parse_exif(photo1_metadata)
exif2 = parse_exif(photo2_metadata)

comparison = compare_exif_data(exif1, exif2)

# Show what's different
for field, info in comparison.items():
    if not info.get("match"):
        print(f"{field}: {info['source1']} vs {info['source2']}")
```

### Group by Category
```python
from app.exif_utils import parse_exif, group_exif_data

exif = parse_exif(metadata)
grouped = group_exif_data(exif)

# Access specific categories
camera = grouped["Camera"]      # Make, model, lens
exposure = grouped["Exposure"]  # ISO, aperture, shutter speed
location = grouped["Location"]  # Lat, lon, altitude
```

## 📁 What's Included

```
backend/
├── app/
│   ├── exif_utils.py              ← Main utility (423 lines)
│   └── EXIF_UTILS_README.md       ← Full API docs (214 lines)
├── tests/unit/
│   └── test_exif_utils.py         ← 36 tests (507 lines)
├── demo_exif_comparison.py        ← Interactive demo (143 lines)
├── EXIF_COMPARISON_SUMMARY.md     ← Implementation summary (240 lines)
└── QUICKSTART_EXIF.md             ← This file
```

## 🎯 Key Features

1. **Parse Both Formats** - iCloud and macOS Photos
2. **Auto-Detection** - Automatically identifies format type
3. **Normalization** - Both formats → same ExifData structure
4. **Grouping** - Organize by Camera, Exposure, Location, etc.
5. **Pretty Print** - Human-readable formatted output
6. **Comparison** - Field-by-field diff between photos

## 📊 Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| macOS Parsing | 6 | ✅ Pass |
| iCloud Parsing | 6 | ✅ Pass |
| Auto-Detection | 4 | ✅ Pass |
| Grouping | 4 | ✅ Pass |
| Pretty Print | 4 | ✅ Pass |
| Comparison | 3 | ✅ Pass |
| Multiple Samples | 4 | ✅ Pass |
| Edge Cases | 5 | ✅ Pass |
| **TOTAL** | **36** | **✅ 100%** |

## 🔍 What's Parsed

### From macOS Format
- Camera: Make, Model, Lens
- Exposure: ISO, Aperture, Shutter Speed, Focal Length, Flash, White Balance
- Location: Latitude, Longitude
- DateTime: Date, Timezone Offset, Timezone Name
- Image: Width, Height, Orientation
- Video: Duration, FPS, Bit Rate, Codec

### From iCloud Format
- Location: Latitude, Longitude, Altitude, Accuracy (Horizontal/Vertical)
- DateTime: Date (high precision), Timezone Offset
- Image: Width, Height, Orientation

## 🎨 Example Output

```
Camera:
-------
  Make: Apple
  Model: iPhone 14 Pro
  Lens: iPhone 14 Pro back dual wide camera 6.86mm f/1.78

Exposure:
---------
  ISO: 80
  Aperture: f/1.78
  Shutter Speed: 1/2202
  Focal Length: 6.86mm

Location:
---------
  Latitude: 47.47891666666666
  Longitude: -122.30338333333333

DateTime:
---------
  Date: 2024-06-08T13:06:51.744000-07:00
  Timezone Offset: -25200s
  Timezone Name: GMT-0700

Image:
------
  Width: 3024
  Height: 4032
  Orientation: 6
```

## 🔧 Advanced Usage

### Force Specific Format
```python
# If you know the format
icloud_exif = parse_exif(data, format_hint="icloud")
macos_exif = parse_exif(data, format_hint="macos")
```

### Show Empty Fields
```python
# Include fields with no data
output = pretty_print_exif(exif, show_empty=True)
```

### Access Raw Data
```python
# Original unprocessed data preserved
raw = exif.raw_data
source = raw["source"]  # "icloud" or "macos"
```

## 📚 More Information

- **Full API Documentation**: `app/EXIF_UTILS_README.md`
- **Implementation Details**: `EXIF_COMPARISON_SUMMARY.md`
- **Test Suite**: `tests/unit/test_exif_utils.py`
- **Demo Script**: `demo_exif_comparison.py`

## ✅ Verification

Verify your installation works:
```bash
cd backend
python -c "from app.exif_utils import parse_exif; print('✅ EXIF utilities ready!')"
```

## 🐛 Troubleshooting

**Import error?**
```bash
# Make sure you're in the backend directory
cd backend
pip install -e .
```

**Tests not running?**
```bash
# Install test dependencies
pip install -e ".[test]"
```

## 🎓 Learn More

1. Start with the **demo**: `python demo_exif_comparison.py`
2. Read the **README**: `app/EXIF_UTILS_README.md`
3. Check the **tests**: `tests/unit/test_exif_utils.py`
4. Review the **summary**: `EXIF_COMPARISON_SUMMARY.md`

---

**Ready to use!** The utilities are production-ready with 36 tests passing and full documentation.
