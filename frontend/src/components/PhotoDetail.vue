<template>
  <div v-if="photo" class="modal" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <button class="modal-close" @click="$emit('close')">×</button>
      
      <div class="detail-container">
        <!-- Left side: Image -->
        <div class="image-section">
          <img :src="detailImageUrl" :alt="photo.original_filename" />
        </div>

        <!-- Right side: Metadata -->
        <div class="metadata-section">
          <h2>{{ photo.original_filename }}</h2>
          
          <!-- Basic Information -->
          <div class="metadata-group">
            <h3>Basic Information</h3>
            <div class="metadata-item">
              <span class="label">Uploaded:</span>
              <span class="value">{{ formatDate(photo.uploaded_at) }}</span>
            </div>
            <div class="metadata-item" v-if="photo.date">
              <span class="label">Date Taken:</span>
              <span class="value">{{ formatDate(photo.date) }}</span>
            </div>
            <div class="metadata-item" v-if="photo.file_size">
              <span class="label">File Size:</span>
              <span class="value">{{ formatFileSize(photo.file_size) }}</span>
            </div>
            <div class="metadata-item" v-if="photo.width && photo.height">
              <span class="label">Dimensions:</span>
              <span class="value">{{ photo.width }} × {{ photo.height }}</span>
            </div>
            <div class="metadata-item" v-if="photo.title">
              <span class="label">Title:</span>
              <span class="value">{{ photo.title }}</span>
            </div>
            <div class="metadata-item" v-if="photo.description">
              <span class="label">Description:</span>
              <span class="value">{{ photo.description }}</span>
            </div>
          </div>

          <!-- Photo Properties -->
          <div class="metadata-group" v-if="hasPhotoProperties">
            <h3>Photo Properties</h3>
            <div class="tags">
              <span v-if="photo.favorite" class="tag favorite">⭐ Favorite</span>
              <span v-if="photo.hidden" class="tag">👁️ Hidden</span>
              <span v-if="photo.isphoto" class="tag">📷 Photo</span>
              <span v-if="photo.ismovie" class="tag">🎬 Movie</span>
              <span v-if="photo.burst" class="tag">📸 Burst</span>
              <span v-if="photo.live_photo" class="tag">🔴 Live Photo</span>
              <span v-if="photo.portrait" class="tag">👤 Portrait</span>
              <span v-if="photo.screenshot" class="tag">🖥️ Screenshot</span>
              <span v-if="photo.slow_mo" class="tag">🐌 Slow-mo</span>
              <span v-if="photo.time_lapse" class="tag">⏱️ Time-lapse</span>
              <span v-if="photo.hdr" class="tag">🌈 HDR</span>
              <span v-if="photo.selfie" class="tag">🤳 Selfie</span>
              <span v-if="photo.panorama" class="tag">🏞️ Panorama</span>
            </div>
          </div>

          <!-- Albums -->
          <div class="metadata-group" v-if="photo.albums && photo.albums.length > 0">
            <h3>Albums</h3>
            <div class="tags">
              <span v-for="album in photo.albums" :key="album" class="tag album">
                📁 {{ album }}
              </span>
            </div>
          </div>

          <!-- Keywords -->
          <div class="metadata-group" v-if="photo.keywords && photo.keywords.length > 0">
            <h3>Keywords</h3>
            <div class="tags">
              <span v-for="keyword in photo.keywords" :key="keyword" class="tag keyword">
                🏷️ {{ keyword }}
              </span>
            </div>
          </div>

          <!-- Labels -->
          <div class="metadata-group" v-if="photo.labels && photo.labels.length > 0">
            <h3>Labels</h3>
            <div class="tags">
              <span v-for="label in photo.labels" :key="label" class="tag label">
                {{ label }}
              </span>
            </div>
          </div>

          <!-- People -->
          <div class="metadata-group" v-if="photo.persons && photo.persons.length > 0">
            <h3>People</h3>
            <div class="tags">
              <span v-for="person in photo.persons" :key="person" class="tag person">
                👤 {{ person }}
              </span>
            </div>
          </div>

          <!-- Location -->
          <div class="metadata-group" v-if="photo.latitude != null && photo.longitude != null">
            <h3>Location</h3>
            <div class="metadata-item">
              <span class="label">Coordinates:</span>
              <span class="value">
                {{ photo.latitude.toFixed(6) }}, {{ photo.longitude.toFixed(6) }}
              </span>
            </div>
            <div class="metadata-item" v-if="photo.place">
              <span class="label">Place:</span>
              <span class="value">{{ formatPlace(photo.place) }}</span>
            </div>
          </div>

          <!-- EXIF Data -->
          <div class="metadata-group" v-if="photo.exif && Object.keys(photo.exif).length > 0">
            <h3>EXIF Data</h3>
            <div class="metadata-item" v-for="(value, key) in formatExif(photo.exif)" :key="key">
              <span class="label">{{ key }}:</span>
              <span class="value">{{ value }}</span>
            </div>
          </div>

          <!-- Technical Details -->
          <div class="metadata-group">
            <h3>Technical Details</h3>
            <div class="metadata-item">
              <span class="label">UUID:</span>
              <span class="value code">{{ photo.uuid }}</span>
            </div>
            <div class="metadata-item" v-if="photo.masterFingerprint">
              <span class="label">Fingerprint:</span>
              <span class="value code">{{ photo.masterFingerprint }}</span>
            </div>
            <div class="metadata-item" v-if="photo.library">
              <span class="label">Library:</span>
              <span class="value">{{ photo.library }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Photo } from "../types/api";

interface PhotoDetailProps {
  photo: Photo | null;
}

interface PhotoDetailEmits {
  (e: "close"): void;
}

const props = defineProps<PhotoDetailProps>();
defineEmits<PhotoDetailEmits>();

// Compute detail image URL - prioritize medium or original over thumbnail
const detailImageUrl = computed(() => {
  if (!props.photo) return "";
  
  // Use environment variable or default to production URL
  const S3_BASE_URL = import.meta.env.VITE_S3_BASE_URL || "https://photos.melloy.life";
  
  const buildS3Url = (s3Path: string | undefined): string | null => {
    if (!s3Path) return null;
    // If already a full URL, return as-is
    if (s3Path.startsWith("http://") || s3Path.startsWith("https://")) {
      return s3Path;
    }
    // Otherwise, construct URL with base domain
    const cleanPath = s3Path.startsWith("/") ? s3Path.substring(1) : s3Path;
    return `${S3_BASE_URL}/${cleanPath}`;
  };
  
  // Prioritize medium (s3_key_path), then original, then edited, then thumbnail
  // This is different from the backend's url property which prioritizes thumbnail first
  const url = 
    buildS3Url(props.photo.s3_key_path) ||
    buildS3Url(props.photo.s3_original_path) ||
    buildS3Url(props.photo.s3_edited_path) ||
    buildS3Url(props.photo.s3_thumbnail_path) ||
    props.photo.url || // Fallback to the computed url from backend
    "";
  
  return url;
});

const formatDate = (dateString?: string): string => {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatFileSize = (bytes?: number): string => {
  if (!bytes) return "Unknown";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
};

const formatPlace = (place: Record<string, any>): string => {
  if (!place) return "";
  
  // Try common place properties
  const parts = [];
  if (place.name) parts.push(place.name);
  if (place.city) parts.push(place.city);
  if (place.state) parts.push(place.state);
  if (place.country) parts.push(place.country);
  
  return parts.join(", ") || JSON.stringify(place);
};

const formatExifValue = (key: string, value: any): string => {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  // Format exposure time (shutter speed)
  if (key === "ExposureTime" || key === "ShutterSpeedValue") {
    const num = parseFloat(value);
    if (num < 1) {
      // Convert to fraction for fast shutter speeds
      const denominator = Math.round(1 / num);
      return `1/${denominator}s`;
    }
    return `${num}s`;
  }

  // Format aperture
  if (key === "FNumber" || key === "ApertureValue") {
    const num = parseFloat(value);
    return `f/${num.toFixed(1)}`;
  }

  // Format focal length
  if (key === "FocalLength") {
    const num = parseFloat(value);
    return `${num.toFixed(0)}mm`;
  }

  // Format ISO
  if (key === "ISO" || key === "ISOSpeedRatings" || key === "PhotographicSensitivity") {
    return `ISO ${value}`;
  }

  // Format flash
  if (key === "Flash") {
    const flashValue = parseInt(value);
    if (flashValue === 0) return "No Flash";
    if (flashValue === 1) return "Fired";
    if (flashValue === 5) return "Fired, Return not detected";
    if (flashValue === 7) return "Fired, Return detected";
    if (flashValue === 9) return "On, Fired";
    if (flashValue === 13) return "On, Return not detected";
    if (flashValue === 15) return "On, Return detected";
    if (flashValue === 16) return "Off, Did not fire";
    if (flashValue === 24) return "Auto, Did not fire";
    if (flashValue === 25) return "Auto, Fired";
    if (flashValue === 29) return "Auto, Fired, Return not detected";
    if (flashValue === 31) return "Auto, Fired, Return detected";
    return `Flash ${value}`;
  }

  // Format white balance
  if (key === "WhiteBalance") {
    if (value === 0) return "Auto";
    if (value === 1) return "Manual";
    return String(value);
  }

  // Format exposure program
  if (key === "ExposureProgram") {
    const programs: Record<number, string> = {
      0: "Not defined",
      1: "Manual",
      2: "Normal program",
      3: "Aperture priority",
      4: "Shutter priority",
      5: "Creative program",
      6: "Action program",
      7: "Portrait mode",
      8: "Landscape mode",
    };
    return programs[parseInt(value)] || String(value);
  }

  // Format metering mode
  if (key === "MeteringMode") {
    const modes: Record<number, string> = {
      0: "Unknown",
      1: "Average",
      2: "Center-weighted average",
      3: "Spot",
      4: "Multi-spot",
      5: "Pattern",
      6: "Partial",
      255: "Other",
    };
    return modes[parseInt(value)] || String(value);
  }

  // Format orientation
  if (key === "Orientation") {
    const orientations: Record<number, string> = {
      1: "Normal",
      2: "Mirrored horizontal",
      3: "Rotated 180°",
      4: "Mirrored vertical",
      5: "Mirrored horizontal then rotated 270° CW",
      6: "Rotated 90° CW",
      7: "Mirrored horizontal then rotated 90° CW",
      8: "Rotated 270° CW",
    };
    return orientations[parseInt(value)] || String(value);
  }

  return String(value);
};

const formatExif = (exif: Record<string, any>): Record<string, string> => {
  const formatted: Record<string, string> = {};
  
  // Common EXIF fields with friendly names
  const fieldMappings: Record<string, string> = {
    Make: "Camera Make",
    Model: "Camera Model",
    LensModel: "Lens Model",
    LensMake: "Lens Make",
    FNumber: "Aperture",
    ApertureValue: "Aperture",
    ExposureTime: "Shutter Speed",
    ShutterSpeedValue: "Shutter Speed",
    ISO: "ISO",
    ISOSpeedRatings: "ISO",
    PhotographicSensitivity: "ISO",
    FocalLength: "Focal Length",
    FocalLengthIn35mmFilm: "Focal Length (35mm equiv)",
    DateTimeOriginal: "Date Taken",
    DateTime: "Modified",
    Flash: "Flash",
    WhiteBalance: "White Balance",
    ExposureProgram: "Exposure Mode",
    MeteringMode: "Metering Mode",
    ExposureBiasValue: "Exposure Compensation",
    ExposureMode: "Exposure Mode",
    ColorSpace: "Color Space",
    Software: "Software",
    Artist: "Artist",
    Copyright: "Copyright",
    Orientation: "Orientation",
    ResolutionUnit: "Resolution Unit",
    XResolution: "X Resolution",
    YResolution: "Y Resolution",
  };

  // Process EXIF data with priority on more important fields
  const priorityOrder = [
    "Make", "Model", "LensModel", "FocalLength", "FocalLengthIn35mmFilm",
    "FNumber", "ApertureValue", "ExposureTime", "ShutterSpeedValue",
    "ISO", "ISOSpeedRatings", "PhotographicSensitivity",
    "ExposureProgram", "ExposureMode", "MeteringMode", "ExposureBiasValue",
    "Flash", "WhiteBalance", "DateTimeOriginal"
  ];

  // Add priority fields first
  for (const key of priorityOrder) {
    if (exif[key] !== null && exif[key] !== undefined && exif[key] !== "") {
      const displayKey = fieldMappings[key] || key;
      const formattedValue = formatExifValue(key, exif[key]);
      if (formattedValue && !formatted[displayKey]) {
        formatted[displayKey] = formattedValue;
      }
    }
  }

  // Add remaining fields
  for (const [key, value] of Object.entries(exif)) {
    if (value !== null && value !== undefined && value !== "") {
      const displayKey = fieldMappings[key] || key;
      if (!formatted[displayKey]) {
        const formattedValue = formatExifValue(key, value);
        formatted[displayKey] = formattedValue;
      }
    }
  }

  return formatted;
};

const hasPhotoProperties = computed(() => {
  return (
    props.photo?.favorite ||
    props.photo?.hidden ||
    props.photo?.isphoto ||
    props.photo?.ismovie ||
    props.photo?.burst ||
    props.photo?.live_photo ||
    props.photo?.portrait ||
    props.photo?.screenshot ||
    props.photo?.slow_mo ||
    props.photo?.time_lapse ||
    props.photo?.hdr ||
    props.photo?.selfie ||
    props.photo?.panorama
  );
});
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
  overflow-y: auto;
}

.modal-content {
  position: relative;
  width: 100%;
  max-width: 1400px;
  background: #1e1e1e;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.95);
}

.detail-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 0;
  min-height: 600px;
}

@media (max-width: 1024px) {
  .detail-container {
    grid-template-columns: 1fr;
  }
}

.image-section {
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.image-section img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 8px;
}

.metadata-section {
  padding: 2rem;
  overflow-y: auto;
  max-height: 90vh;
  background: #1e1e1e;
}

.metadata-section h2 {
  margin: 0 0 1.5rem 0;
  color: #e0e0e0;
  font-size: 1.5rem;
  word-break: break-word;
}

.metadata-group {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #3a3a3a;
}

.metadata-group:last-child {
  border-bottom: none;
}

.metadata-group h3 {
  margin: 0 0 1rem 0;
  color: #667eea;
  font-size: 1.1rem;
  font-weight: 600;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.metadata-item .label {
  color: #b0b0b0;
  font-weight: 500;
  min-width: 140px;
  flex-shrink: 0;
}

.metadata-item .value {
  color: #e0e0e0;
  text-align: right;
  word-break: break-word;
}

.metadata-item .value.code {
  font-family: "Courier New", monospace;
  font-size: 0.875rem;
  background: #2a2a2a;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  display: inline-block;
  padding: 0.4rem 0.8rem;
  background: #2a2a2a;
  color: #e0e0e0;
  border-radius: 16px;
  font-size: 0.875rem;
  border: 1px solid #3a3a3a;
}

.tag.favorite {
  background: #fbbf24;
  color: #1e1e1e;
  border-color: #f59e0b;
  font-weight: 600;
}

.tag.album {
  background: #667eea;
  color: white;
  border-color: #5568d3;
}

.tag.keyword {
  background: #10b981;
  color: white;
  border-color: #059669;
}

.tag.label {
  background: #8b5cf6;
  color: white;
  border-color: #7c3aed;
}

.tag.person {
  background: #ec4899;
  color: white;
  border-color: #db2777;
}

/* Scrollbar styling */
.metadata-section::-webkit-scrollbar {
  width: 8px;
}

.metadata-section::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.metadata-section::-webkit-scrollbar-thumb {
  background: #3a3a3a;
  border-radius: 4px;
}

.metadata-section::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}
</style>
