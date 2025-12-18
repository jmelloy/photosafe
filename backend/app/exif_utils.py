"""EXIF data parsing and normalization utilities for iCloud and macOS formats"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class ExifData:
    """Normalized EXIF data structure"""
    
    # Camera information
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    
    # Exposure settings
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[float] = None
    focal_length: Optional[float] = None
    exposure_bias: Optional[float] = None
    flash_fired: Optional[bool] = None
    white_balance: Optional[int] = None
    metering_mode: Optional[int] = None
    
    # Location information
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    
    # Date and time
    date: Optional[datetime] = None
    tzoffset: Optional[int] = None
    tzname: Optional[str] = None
    
    # Image properties
    width: Optional[int] = None
    height: Optional[int] = None
    orientation: Optional[int] = None
    
    # Video properties
    duration: Optional[float] = None
    fps: Optional[float] = None
    bit_rate: Optional[int] = None
    codec: Optional[str] = None
    
    # Additional metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)


def parse_macos_exif(data: Dict[str, Any]) -> ExifData:
    """
    Parse EXIF data from macOS Photos format.
    
    macOS format has a structured 'exif_info' field with all EXIF data.
    
    Args:
        data: Dictionary containing macOS Photos metadata
        
    Returns:
        ExifData object with normalized EXIF information
    """
    exif_info = data.get("exif_info", {}) or {}
    
    # Parse date
    date = None
    if exif_info.get("date"):
        try:
            date_str = exif_info["date"]
            # Handle ISO format with timezone
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
    elif data.get("date"):
        try:
            date_str = data["date"]
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
    
    return ExifData(
        # Camera information
        camera_make=exif_info.get("camera_make"),
        camera_model=exif_info.get("camera_model"),
        lens_model=exif_info.get("lens_model"),
        
        # Exposure settings
        iso=exif_info.get("iso"),
        aperture=exif_info.get("aperture"),
        shutter_speed=exif_info.get("shutter_speed"),
        focal_length=exif_info.get("focal_length"),
        exposure_bias=exif_info.get("exposure_bias"),
        flash_fired=exif_info.get("flash_fired"),
        white_balance=exif_info.get("white_balance"),
        metering_mode=exif_info.get("metering_mode"),
        
        # Location information
        latitude=exif_info.get("latitude") or data.get("latitude"),
        longitude=exif_info.get("longitude") or data.get("longitude"),
        
        # Date and time
        date=date,
        tzoffset=exif_info.get("tzoffset"),
        tzname=exif_info.get("tzname"),
        
        # Image properties
        width=data.get("width") or data.get("original_width"),
        height=data.get("height") or data.get("original_height"),
        orientation=data.get("orientation") or data.get("original_orientation"),
        
        # Video properties
        duration=exif_info.get("duration"),
        fps=exif_info.get("fps"),
        bit_rate=exif_info.get("bit_rate"),
        codec=exif_info.get("codec"),
        
        # Store raw data
        raw_data={"exif_info": exif_info, "source": "macos"}
    )


def parse_icloud_exif(data: Dict[str, Any]) -> ExifData:
    """
    Parse EXIF data from iCloud format.
    
    iCloud format has nested structure with:
    - asset_fields: Contains top-level photo metadata
    - fields: Contains detailed EXIF-like data with numeric and string keys
    - location: GPS coordinates and accuracy
    
    Args:
        data: Dictionary containing iCloud metadata
        
    Returns:
        ExifData object with normalized EXIF information
    """
    asset_fields = data.get("asset_fields", {}) or {}
    fields = data.get("fields", {}) or {}
    location = asset_fields.get("location", {}) or {}
    
    # Parse date from timestamp (milliseconds since epoch)
    date = None
    if asset_fields.get("assetDate"):
        try:
            timestamp_ms = asset_fields["assetDate"]
            # Convert milliseconds to seconds
            date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        except (ValueError, TypeError):
            pass
    
    # Extract camera information from fields
    # Note: iCloud format stores EXIF in numeric/string keys which vary
    # We extract what we can find
    camera_make = None
    camera_model = None
    lens_model = None
    
    # Try to find camera info in fields
    if isinstance(fields, dict):
        # Look for potential camera make/model in string values
        for key, value in fields.items():
            if isinstance(value, str):
                if "iPhone" in value or "Apple" in value:
                    if not camera_make and "Apple" in value:
                        camera_make = "Apple"
                    if "iPhone" in value:
                        camera_model = value
    
    # Get timezone offset
    tzoffset = asset_fields.get("timeZoneOffset")
    
    # Parse orientation
    orientation = asset_fields.get("orientation")
    
    # Get dimensions from fields
    width = None
    height = None
    if "resOriginalWidth" in fields:
        width = fields.get("resOriginalWidth")
    if "resOriginalHeight" in fields:
        height = fields.get("resOriginalHeight")
    
    return ExifData(
        # Camera information (limited in iCloud format)
        camera_make=camera_make,
        camera_model=camera_model,
        lens_model=lens_model,
        
        # Location information
        latitude=location.get("lat"),
        longitude=location.get("lon"),
        altitude=location.get("alt"),
        horizontal_accuracy=location.get("horzAcc"),
        vertical_accuracy=location.get("vertAcc"),
        
        # Date and time
        date=date,
        tzoffset=tzoffset,
        
        # Image properties
        width=width,
        height=height,
        orientation=orientation,
        
        # Store raw data
        raw_data={
            "asset_fields": asset_fields,
            "fields": fields,
            "location": location,
            "source": "icloud"
        }
    )


def parse_exif(data: Dict[str, Any], format_hint: Optional[str] = None) -> ExifData:
    """
    Parse EXIF data from either iCloud or macOS format.
    
    Auto-detects format based on structure if format_hint is not provided.
    
    Args:
        data: Dictionary containing photo metadata
        format_hint: Optional hint about the format ("icloud" or "macos")
        
    Returns:
        ExifData object with normalized EXIF information
    """
    # Auto-detect format if not specified
    if format_hint is None:
        if "exif_info" in data:
            format_hint = "macos"
        elif "asset_fields" in data or "_asset_record" in data:
            format_hint = "icloud"
        else:
            # Default to macos if we can't determine
            format_hint = "macos"
    
    if format_hint == "icloud":
        return parse_icloud_exif(data)
    else:
        return parse_macos_exif(data)


def group_exif_data(exif: ExifData) -> Dict[str, Dict[str, Any]]:
    """
    Group EXIF data by category for easier display.
    
    Args:
        exif: ExifData object
        
    Returns:
        Dictionary with categorized EXIF fields
    """
    return {
        "Camera": {
            "Make": exif.camera_make,
            "Model": exif.camera_model,
            "Lens": exif.lens_model,
        },
        "Exposure": {
            "ISO": exif.iso,
            "Aperture": f"f/{exif.aperture}" if exif.aperture else None,
            "Shutter Speed": f"1/{int(1/exif.shutter_speed)}" if exif.shutter_speed and exif.shutter_speed > 0.0001 else (f"{exif.shutter_speed}s" if exif.shutter_speed else None),
            "Focal Length": f"{exif.focal_length}mm" if exif.focal_length else None,
            "Exposure Bias": exif.exposure_bias,
            "Flash Fired": exif.flash_fired,
            "White Balance": exif.white_balance,
            "Metering Mode": exif.metering_mode,
        },
        "Location": {
            "Latitude": exif.latitude,
            "Longitude": exif.longitude,
            "Altitude": f"{exif.altitude}m" if exif.altitude else None,
            "Horizontal Accuracy": f"{exif.horizontal_accuracy}m" if exif.horizontal_accuracy else None,
            "Vertical Accuracy": f"{exif.vertical_accuracy}m" if exif.vertical_accuracy else None,
        },
        "DateTime": {
            "Date": exif.date.isoformat() if exif.date else None,
            "Timezone Offset": f"{exif.tzoffset}s" if exif.tzoffset else None,
            "Timezone Name": exif.tzname,
        },
        "Image": {
            "Width": exif.width,
            "Height": exif.height,
            "Orientation": exif.orientation,
        },
        "Video": {
            "Duration": f"{exif.duration}s" if exif.duration else None,
            "FPS": exif.fps,
            "Bit Rate": exif.bit_rate,
            "Codec": exif.codec,
        },
    }


def pretty_print_exif(exif: ExifData, show_empty: bool = False) -> str:
    """
    Create a human-readable formatted string of EXIF data.
    
    Args:
        exif: ExifData object to format
        show_empty: Whether to show fields with None values
        
    Returns:
        Formatted string with EXIF information
    """
    grouped = group_exif_data(exif)
    lines = []
    
    for category, fields in grouped.items():
        # Filter out None values if show_empty is False
        if not show_empty:
            fields = {k: v for k, v in fields.items() if v is not None}
        
        if fields:  # Only show category if it has data
            lines.append(f"\n{category}:")
            lines.append("-" * (len(category) + 1))
            
            for field_name, value in fields.items():
                if value is not None:
                    lines.append(f"  {field_name}: {value}")
                elif show_empty:
                    lines.append(f"  {field_name}: (not set)")
    
    return "\n".join(lines)


def compare_exif_data(exif1: ExifData, exif2: ExifData) -> Dict[str, Dict[str, Any]]:
    """
    Compare two ExifData objects and return the differences.
    
    Args:
        exif1: First ExifData object
        exif2: Second ExifData object
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {}
    
    # Get all field names from ExifData
    fields = [
        "camera_make", "camera_model", "lens_model",
        "iso", "aperture", "shutter_speed", "focal_length", "exposure_bias",
        "flash_fired", "white_balance", "metering_mode",
        "latitude", "longitude", "altitude", "horizontal_accuracy", "vertical_accuracy",
        "date", "tzoffset", "tzname",
        "width", "height", "orientation",
        "duration", "fps", "bit_rate", "codec"
    ]
    
    for field_name in fields:
        val1 = getattr(exif1, field_name)
        val2 = getattr(exif2, field_name)
        
        if val1 != val2:
            comparison[field_name] = {
                "source1": val1,
                "source2": val2,
                "match": False
            }
        elif val1 is not None:  # Only record matches if there's actual data
            comparison[field_name] = {
                "value": val1,
                "match": True
            }
    
    return comparison
