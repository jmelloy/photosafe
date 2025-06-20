import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import piexif
import requests
from PIL import ExifTags, Image
from task_processor import TaskConsumer, TaskProcessor, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ExifProcessingConfig(Config):
    # List of EXIF tags to extract (empty means all)
    target_tags: List[str] = None
    # Whether to include GPS data
    include_gps: bool = True
    # Whether to process extended XMP metadata
    process_xmp: bool = True


class ExifProcessor(TaskProcessor):
    """Processor for extracting and analyzing EXIF data from images"""

    def __init__(self, config: ExifProcessingConfig):
        super().__init__()
        self.config = config

        # Initialize EXIF tag mappings
        self.exif_mappings = {
            "Make": "camera_make",
            "Model": "camera_model",
            "DateTime": "capture_time",
            "ExposureTime": "exposure_time",
            "FNumber": "f_number",
            "ISOSpeedRatings": "iso_speed",
            "FocalLength": "focal_length",
            "LensModel": "lens_model",
            "Software": "software",
            "Artist": "artist",
            "Copyright": "copyright",
        }

    def process_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image EXIF data"""
        image_url = task_data["image_url"]
        task_id = task_data["task_id"]

        # Download image
        image_data = self._download_image(image_url)

        # Extract EXIF data
        exif_data = self._extract_exif(image_data)

        # Process GPS data if present and enabled
        if self.config.include_gps and "GPSInfo" in exif_data:
            exif_data["location"] = self._process_gps_data(exif_data["GPSInfo"])

        # Clean and format the data
        formatted_data = self._format_exif_data(exif_data)

        # Add analysis and insights
        formatted_data["insights"] = self._analyze_exif_data(formatted_data)

        return {
            "task_id": task_id,
            "metadata": formatted_data,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    def _extract_exif(self, image_data: bytes) -> Dict[str, Any]:
        """Extract EXIF data from image"""
        result = {}

        try:
            with Image.open(BytesIO(image_data)) as img:
                # Get basic image info
                result["image_info"] = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                }

                # Extract EXIF data
                if hasattr(img, "_getexif"):
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))

                            # Filter tags if specific ones are requested
                            if (
                                self.config.target_tags
                                and tag_name not in self.config.target_tags
                            ):
                                continue

                            # Special handling for GPS data
                            if tag_name == "GPSInfo" and self.config.include_gps:
                                result["GPSInfo"] = {
                                    ExifTags.GPSTAGS.get(t, str(t)): v
                                    for t, v in value.items()
                                }
                            else:
                                result[tag_name] = value

                # Extract XMP data if enabled
                if self.config.process_xmp:
                    xmp_data = self._extract_xmp(img)
                    if xmp_data:
                        result["xmp"] = xmp_data

        except Exception as e:
            logger.error(f"Error extracting EXIF data: {e}")
            raise

        return result

    def _extract_xmp(self, img: Image) -> Optional[Dict[str, Any]]:
        """Extract XMP metadata if available"""
        try:
            if hasattr(img, "info") and "XML:com.adobe.xmp" in img.info:
                return self._parse_xmp(img.info["XML:com.adobe.xmp"])
        except Exception as e:
            logger.warning(f"Error extracting XMP data: {e}")
        return None

    def _process_gps_data(self, gps_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process GPS data into a more useful format"""
        try:
            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                lat = self._convert_to_degrees(gps_info["GPSLatitude"])
                lon = self._convert_to_degrees(gps_info["GPSLongitude"])

                if gps_info.get("GPSLatitudeRef", "N") == "S":
                    lat = -lat
                if gps_info.get("GPSLongitudeRef", "E") == "W":
                    lon = -lon

                return {
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": self._process_altitude(gps_info.get("GPSAltitude")),
                    "timestamp": self._process_gps_timestamp(gps_info),
                }
        except Exception as e:
            logger.warning(f"Error processing GPS data: {e}")
        return None

    def _convert_to_degrees(self, value: tuple) -> float:
        """Convert GPS coordinates to degrees"""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    def _process_altitude(self, altitude) -> Optional[float]:
        """Process GPS altitude data"""
        if altitude:
            if isinstance(altitude, tuple):
                return float(altitude[0]) / float(altitude[1])
            return float(altitude)
        return None

    def _format_exif_data(self, exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format and clean EXIF data for output"""
        formatted = {}

        for tag, value in exif_data.items():
            # Map common EXIF tags to friendly names
            friendly_name = self.exif_mappings.get(tag, tag)

            # Format specific types of data
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8")
                except UnicodeDecodeError:
                    value = value.hex()
            elif isinstance(value, tuple) and len(value) == 2:
                # Handle rational numbers
                try:
                    value = float(value[0]) / float(value[1])
                except (ZeroDivisionError, TypeError):
                    continue

            formatted[friendly_name] = value

        return formatted

    def _analyze_exif_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze EXIF data for insights"""
        insights = {}

        # Analyze image quality indicators
        if "iso_speed" in data and "f_number" in data:
            insights["quality_indicators"] = self._analyze_quality(data)

        # Check for editing software
        if "software" in data:
            insights["edited"] = True
            insights["editing_software"] = data["software"]

        # Analyze camera settings
        if "exposure_time" in data and "f_number" in data:
            insights["shooting_conditions"] = self._analyze_shooting_conditions(data)

        return insights

    def _analyze_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image quality based on camera settings"""
        quality_info = {}

        if "iso_speed" in data:
            iso = float(data["iso_speed"])
            if iso <= 100:
                quality_info["noise_level"] = "minimal"
            elif iso <= 400:
                quality_info["noise_level"] = "low"
            elif iso <= 1600:
                quality_info["noise_level"] = "moderate"
            else:
                quality_info["noise_level"] = "high"

        if "f_number" in data:
            f_number = float(data["f_number"])
            if f_number <= 2.8:
                quality_info["depth_of_field"] = "shallow"
            elif f_number <= 8:
                quality_info["depth_of_field"] = "medium"
            else:
                quality_info["depth_of_field"] = "deep"

        return quality_info

    def _analyze_shooting_conditions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze shooting conditions based on camera settings"""
        conditions = {}

        if "exposure_time" in data:
            exposure = float(data["exposure_time"])
            if exposure < 1 / 1000:
                conditions["motion_handling"] = "action/sports"
            elif exposure < 1 / 60:
                conditions["motion_handling"] = "handheld"
            else:
                conditions["motion_handling"] = "tripod recommended"

        return conditions


if __name__ == "__main__":
    # Configuration
    config = ExifProcessingConfig(
        api_timeout=int(os.environ.get("API_TIMEOUT", 30)),
        max_retries=int(os.environ.get("MAX_RETRIES", 3)),
        retry_delay=int(os.environ.get("RETRY_DELAY", 5)),
        include_gps=os.environ.get("INCLUDE_GPS", "true").lower() == "true",
        process_xmp=os.environ.get("PROCESS_XMP", "true").lower() == "true",
    )

    # Create processor and consumer
    processor = ExifProcessor(config)
    consumer = TaskConsumer(
        queue_name=os.environ.get("QUEUE_NAME", "exif_processing"),
        processor=processor,
        rabbit_host=os.environ.get("RABBIT_HOST", "localhost"),
    )

    consumer.start()
