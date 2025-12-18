"""Tests for EXIF data parsing and normalization utilities"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone

from app.exif_utils import (
    ExifData,
    parse_macos_exif,
    parse_icloud_exif,
    parse_exif,
    group_exif_data,
    pretty_print_exif,
    compare_exif_data,
)


# Fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def icloud_samples():
    """Load iCloud sample data"""
    with open(FIXTURES_DIR / "icloud_sample.json", "r") as f:
        return json.load(f)


@pytest.fixture
def macos_samples():
    """Load macOS sample data"""
    with open(FIXTURES_DIR / "macos_sample.json", "r") as f:
        return json.load(f)


class TestMacOSExifParsing:
    """Test parsing EXIF data from macOS Photos format"""
    
    def test_parse_macos_basic_fields(self, macos_samples):
        """Test parsing basic EXIF fields from macOS format"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert isinstance(exif, ExifData)
        assert exif.camera_make == "Apple"
        assert exif.camera_model == "iPhone 14 Pro"
        assert exif.lens_model == "iPhone 14 Pro back dual wide camera 6.86mm f/1.78"
    
    def test_parse_macos_exposure_settings(self, macos_samples):
        """Test parsing exposure settings from macOS format"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert exif.iso == 80
        assert exif.aperture == 1.78
        assert exif.shutter_speed is not None
        assert exif.focal_length is not None
        assert exif.flash_fired == False
        assert exif.white_balance == 0
        assert exif.metering_mode == 5
    
    def test_parse_macos_location(self, macos_samples):
        """Test parsing location data from macOS format"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert exif.latitude is not None
        assert exif.longitude is not None
        assert isinstance(exif.latitude, float)
        assert isinstance(exif.longitude, float)
    
    def test_parse_macos_date(self, macos_samples):
        """Test parsing date from macOS format"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert exif.date is not None
        assert isinstance(exif.date, datetime)
        assert exif.tzoffset == -25200
        assert exif.tzname == "GMT-0700"
    
    def test_parse_macos_image_properties(self, macos_samples):
        """Test parsing image properties from macOS format"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert exif.width is not None
        assert exif.height is not None
        assert exif.orientation is not None
        assert isinstance(exif.width, int)
        assert isinstance(exif.height, int)
    
    def test_parse_macos_raw_data(self, macos_samples):
        """Test that raw data is preserved"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        
        assert "exif_info" in exif.raw_data
        assert exif.raw_data["source"] == "macos"


class TestICloudExifParsing:
    """Test parsing EXIF data from iCloud format"""
    
    def test_parse_icloud_basic_structure(self, icloud_samples):
        """Test parsing basic structure from iCloud format"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        assert isinstance(exif, ExifData)
        assert exif.raw_data["source"] == "icloud"
    
    def test_parse_icloud_location(self, icloud_samples):
        """Test parsing location data from iCloud format"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        # iCloud format has detailed location data
        assert exif.latitude is not None
        assert exif.longitude is not None
        assert exif.altitude is not None
        assert exif.horizontal_accuracy is not None
        assert isinstance(exif.latitude, float)
        assert isinstance(exif.longitude, float)
    
    def test_parse_icloud_date(self, icloud_samples):
        """Test parsing date from iCloud format (milliseconds timestamp)"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        assert exif.date is not None
        assert isinstance(exif.date, datetime)
        # Check that timezone is UTC
        assert exif.date.tzinfo == timezone.utc
    
    def test_parse_icloud_timezone_offset(self, icloud_samples):
        """Test parsing timezone offset from iCloud format"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        assert exif.tzoffset is not None
        # iCloud stores timezone offset in seconds
        assert isinstance(exif.tzoffset, int)
    
    def test_parse_icloud_orientation(self, icloud_samples):
        """Test parsing orientation from iCloud format"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        assert exif.orientation is not None
        assert isinstance(exif.orientation, int)
    
    def test_parse_icloud_dimensions(self, icloud_samples):
        """Test parsing image dimensions from iCloud format"""
        sample = icloud_samples[0]
        exif = parse_icloud_exif(sample)
        
        # Dimensions might be in fields
        # Not all iCloud samples may have this data
        if exif.width:
            assert isinstance(exif.width, int)
        if exif.height:
            assert isinstance(exif.height, int)


class TestAutoDetection:
    """Test automatic format detection"""
    
    def test_auto_detect_macos_format(self, macos_samples):
        """Test auto-detection of macOS format"""
        sample = macos_samples[0]
        exif = parse_exif(sample)  # No format_hint
        
        assert exif.raw_data["source"] == "macos"
        assert exif.camera_make == "Apple"
    
    def test_auto_detect_icloud_format(self, icloud_samples):
        """Test auto-detection of iCloud format"""
        sample = icloud_samples[0]
        exif = parse_exif(sample)  # No format_hint
        
        assert exif.raw_data["source"] == "icloud"
    
    def test_explicit_format_hint_macos(self, macos_samples):
        """Test explicit format hint for macOS"""
        sample = macos_samples[0]
        exif = parse_exif(sample, format_hint="macos")
        
        assert exif.raw_data["source"] == "macos"
    
    def test_explicit_format_hint_icloud(self, icloud_samples):
        """Test explicit format hint for iCloud"""
        sample = icloud_samples[0]
        exif = parse_exif(sample, format_hint="icloud")
        
        assert exif.raw_data["source"] == "icloud"


class TestGrouping:
    """Test EXIF data grouping by category"""
    
    def test_group_exif_data_structure(self, macos_samples):
        """Test that grouping creates expected categories"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        grouped = group_exif_data(exif)
        
        # Check all expected categories exist
        assert "Camera" in grouped
        assert "Exposure" in grouped
        assert "Location" in grouped
        assert "DateTime" in grouped
        assert "Image" in grouped
        assert "Video" in grouped
    
    def test_group_exif_data_camera(self, macos_samples):
        """Test camera information grouping"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        grouped = group_exif_data(exif)
        
        camera = grouped["Camera"]
        assert camera["Make"] == "Apple"
        assert camera["Model"] == "iPhone 14 Pro"
        assert camera["Lens"] is not None
    
    def test_group_exif_data_exposure(self, macos_samples):
        """Test exposure information grouping"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        grouped = group_exif_data(exif)
        
        exposure = grouped["Exposure"]
        assert exposure["ISO"] == 80
        assert "f/" in exposure["Aperture"]
        assert exposure["Flash Fired"] == False
    
    def test_group_exif_data_location(self, macos_samples):
        """Test location information grouping"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        grouped = group_exif_data(exif)
        
        location = grouped["Location"]
        assert location["Latitude"] is not None
        assert location["Longitude"] is not None


class TestPrettyPrint:
    """Test pretty printing of EXIF data"""
    
    def test_pretty_print_basic(self, macos_samples):
        """Test basic pretty printing"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        output = pretty_print_exif(exif)
        
        assert isinstance(output, str)
        assert len(output) > 0
        assert "Camera:" in output
        assert "Exposure:" in output
    
    def test_pretty_print_shows_values(self, macos_samples):
        """Test that pretty print shows actual values"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        output = pretty_print_exif(exif)
        
        assert "Apple" in output
        assert "iPhone 14 Pro" in output
        assert "80" in output  # ISO
    
    def test_pretty_print_hide_empty(self, macos_samples):
        """Test that empty fields are hidden by default"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        output = pretty_print_exif(exif, show_empty=False)
        
        # Should not show "(not set)" for empty fields
        assert "(not set)" not in output
    
    def test_pretty_print_show_empty(self, macos_samples):
        """Test showing empty fields when requested"""
        sample = macos_samples[0]
        exif = parse_macos_exif(sample)
        output = pretty_print_exif(exif, show_empty=True)
        
        # Should show "(not set)" for empty fields
        assert "(not set)" in output


class TestComparison:
    """Test comparison of EXIF data from different sources"""
    
    def test_compare_same_photo_different_formats(self, icloud_samples, macos_samples):
        """Test comparing data that should represent the same photo"""
        # Note: The fixtures may not be the exact same photos, 
        # so we're testing the comparison mechanism itself
        icloud_exif = parse_icloud_exif(icloud_samples[0])
        macos_exif = parse_macos_exif(macos_samples[0])
        
        comparison = compare_exif_data(icloud_exif, macos_exif)
        
        assert isinstance(comparison, dict)
        # Check that comparison contains field information
        assert len(comparison) > 0
    
    def test_compare_exif_structure(self, macos_samples):
        """Test comparison result structure"""
        exif1 = parse_macos_exif(macos_samples[0])
        exif2 = parse_macos_exif(macos_samples[1] if len(macos_samples) > 1 else macos_samples[0])
        
        comparison = compare_exif_data(exif1, exif2)
        
        # Each comparison entry should have specific structure
        for field, info in comparison.items():
            if info.get("match"):
                assert "value" in info
            else:
                assert "source1" in info
                assert "source2" in info
                assert info["match"] == False
    
    def test_compare_identical_exif(self, macos_samples):
        """Test comparing identical EXIF data"""
        sample = macos_samples[0]
        exif1 = parse_macos_exif(sample)
        exif2 = parse_macos_exif(sample)
        
        comparison = compare_exif_data(exif1, exif2)
        
        # All compared fields should match
        for field, info in comparison.items():
            assert info["match"] == True


class TestMultipleSamples:
    """Test parsing multiple samples from fixtures"""
    
    def test_parse_all_macos_samples(self, macos_samples):
        """Test that all macOS samples can be parsed without errors"""
        for i, sample in enumerate(macos_samples):
            try:
                exif = parse_macos_exif(sample)
                assert isinstance(exif, ExifData)
            except Exception as e:
                pytest.fail(f"Failed to parse macOS sample {i}: {str(e)}")
    
    def test_parse_all_icloud_samples(self, icloud_samples):
        """Test that all iCloud samples can be parsed without errors"""
        for i, sample in enumerate(icloud_samples):
            try:
                exif = parse_icloud_exif(sample)
                assert isinstance(exif, ExifData)
            except Exception as e:
                pytest.fail(f"Failed to parse iCloud sample {i}: {str(e)}")
    
    def test_consistency_across_macos_samples(self, macos_samples):
        """Test that all macOS samples have consistent structure"""
        for sample in macos_samples:
            exif = parse_macos_exif(sample)
            # All should have source marker
            assert exif.raw_data["source"] == "macos"
    
    def test_consistency_across_icloud_samples(self, icloud_samples):
        """Test that all iCloud samples have consistent structure"""
        for sample in icloud_samples:
            exif = parse_icloud_exif(sample)
            # All should have source marker
            assert exif.raw_data["source"] == "icloud"


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_parse_empty_dict(self):
        """Test parsing empty dictionary"""
        exif = parse_macos_exif({})
        assert isinstance(exif, ExifData)
        assert exif.camera_make is None
    
    def test_parse_missing_exif_info(self):
        """Test parsing macOS data without exif_info"""
        data = {"date": "2024-01-01T00:00:00", "width": 1920, "height": 1080}
        exif = parse_macos_exif(data)
        assert isinstance(exif, ExifData)
        assert exif.width == 1920
    
    def test_parse_missing_asset_fields(self):
        """Test parsing iCloud data without asset_fields"""
        data = {"fields": {}}
        exif = parse_icloud_exif(data)
        assert isinstance(exif, ExifData)
    
    def test_parse_invalid_date(self):
        """Test parsing with invalid date format"""
        data = {"exif_info": {"date": "invalid-date"}}
        exif = parse_macos_exif(data)
        # Should not raise exception, date should be None
        assert exif.date is None
    
    def test_pretty_print_empty_exif(self):
        """Test pretty printing empty EXIF data"""
        exif = ExifData()
        output = pretty_print_exif(exif)
        # Should return empty or minimal output
        assert isinstance(output, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
