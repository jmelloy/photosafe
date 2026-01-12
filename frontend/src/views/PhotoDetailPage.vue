<template>
  <div class="photo-detail-page">
    <!-- Back button -->
    <div class="back-button-container">
      <button @click="goBack" class="back-button">← Back to Gallery</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <LoadingSpinner message="Loading photo..." />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h2>Photo Not Found</h2>
      <p>{{ error }}</p>
      <button @click="goBack" class="back-button-alt">
        Go Back to Gallery
      </button>
    </div>

    <!-- Photo detail content -->
    <div v-else-if="photo" class="detail-container">
      <!-- Left side: Image -->
      <div class="image-section">
        <img :src="detailImageUrl" :alt="photo.original_filename" />
      </div>

      <!-- Right side: Metadata -->
      <div class="metadata-section">
        <div class="photo-header">
          <h2>{{ photo.original_filename }}</h2>
          <button @click="copyLink" class="share-button" :title="copyLinkText">
            {{ copyLinkText }}
          </button>
        </div>

        <!-- Basic Information -->
        <div class="metadata-group">
          <h3>Basic Information</h3>
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
        <div class="metadata-group" v-if="photo.latitude && photo.longitude">
          <h3>Location</h3>
          <div class="metadata-item">
            <span class="label">Coordinates:</span>
            <span class="value">{{ photo.latitude.toFixed(3) }}, {{ photo.longitude.toFixed(3) }}</span>
          </div>
          <div class="metadata-item" v-if="photo.place">
            <span class="label">Place:</span>
            <span class="value">{{ formatPlace(photo.place) }}</span>
          </div>
          <!-- Map -->
          <div class="map-container">
            <PhotoMap :latitude="photo.latitude" :longitude="photo.longitude" :photo-title="photo.original_filename" />
          </div>
        </div>

        <!-- EXIF Data -->
        <div class="metadata-group" v-if="photo.exif && Object.keys(photo.exif).length > 0">
          <h3>EXIF Data</h3>
          <!-- Important fields -->
          <div class="metadata-item" v-for="(value, key) in formattedExif.important" :key="key">
            <span class="label">{{ key }}:</span>
            <span class="value">{{ value }}</span>
          </div>
          <!-- Less important fields (collapsible) -->
          <details v-if="formattedExif.additional && Object.keys(formattedExif.additional).length > 0"
            class="exif-details">
            <summary>Additional EXIF Data</summary>
            <div class="metadata-item" v-for="(value, key) in formattedExif.additional" :key="key">
              <span class="label">{{ key }}:</span>
              <span class="value">{{ value }}</span>
            </div>
          </details>
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getPhoto } from "../api/photos";
import type { Photo } from "../types/api";
import PhotoMap from "../components/PhotoMap.vue";
import LoadingSpinner from "../components/LoadingSpinner.vue";
import { formatPlace } from "../utils/formatPlace";
import { getDetailImageUrl, getShareUrl } from "../utils/imageUrl";
import { formatDate as formatDateUtil, formatFileSize } from "../utils/format";
import { formatApiError, logError } from "../utils/errorHandling";

interface PhotoDetailPageProps {
  uuid: string;
}

const props = defineProps<PhotoDetailPageProps>();
const router = useRouter();

const photo = ref<Photo | null>(null);
const loading = ref<boolean>(true);
const error = ref<string>("");
const copyLinkText = ref<string>("🔗 Share Link");

const loadPhoto = async () => {
  loading.value = true;
  error.value = "";

  try {
    photo.value = await getPhoto(props.uuid);
  } catch (err: unknown) {
    logError("Load photo", err);
    error.value = formatApiError(err);
  } finally {
    loading.value = false;
  }
};

// Compute detail image URL - prioritize medium or original over thumbnail
const detailImageUrl = computed(() => getDetailImageUrl(photo.value));

const goBack = () => {
  router.push("/");
};

const copyLink = async () => {
  // Get the direct S3 URL for the medium/edited version
  const shareUrl = getShareUrl(photo.value);

  if (!shareUrl) {
    copyLinkText.value = "✗ No Share URL";
    setTimeout(() => {
      copyLinkText.value = "🔗 Share Link";
    }, 2000);
    return;
  }

  try {
    await navigator.clipboard.writeText(shareUrl);
    copyLinkText.value = "✓ Link Copied!";
    setTimeout(() => {
      copyLinkText.value = "🔗 Share Link";
    }, 2000);
  } catch (err: unknown) {
    console.error("Failed to copy link:", err);
    copyLinkText.value = "✗ Copy Failed";
    setTimeout(() => {
      copyLinkText.value = "🔗 Share Link";
    }, 2000);
  }
};

const formatDate = (dateString?: string): string => {
  if (!dateString) return "Unknown";

  // Get the offset from EXIF data (e.g., "+05:00" or "-08:00")
  const offsetTime = photo.value?.exif?.OffsetTime || photo.value?.exif?.OffsetTimeOriginal;

  return formatDateUtil(dateString, {
    exifOffset: offsetTime,
  });
};

const formatExifKey = (key: string): string => {
  // Convert camelCase or PascalCase to Title Case with spaces
  return key
    .replace(/([A-Z])/g, " $1") // Add space before capital letters
    .replace(/^./, (str) => str.toUpperCase()) // Capitalize first letter
    .trim();
};

const formatExifValue = (key: string, value: any): string => {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  // Format dates - convert from EXIF format "2025:12:15 14:03:35" to readable format
  if (
    key === "DateTimeOriginal" ||
    key === "DateTimeDigitized" ||
    key === "DateTime"
  ) {

    return String(value);
  }
  if (Array.isArray(value)) {
    // Rational number (fraction) - [numerator, denominator]
    if (value.length === 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
      const result = value[1];

      // Special formatting for specific fields
      if (key === 'FNumber' || key === 'ApertureValue') {
        return `ƒ/${result.toFixed(2)}`;
      }
      if (key === 'ExposureTime') {
        return result >= 1 ? `${result.toFixed(1)}s` : `1/${Math.round(1 / result)}s`;
      }
      if (key === 'FocalLength') {
        return `${result.toFixed(1)}mm`;
      }
      if (key === 'ExposureBiasValue') {
        return result === 0 ? '0 EV' : `${result > 0 ? '+' : ''}${result.toFixed(1)} EV`;
      }
      if (key === 'BrightnessValue') {
        return `${result.toFixed(2)} EV`;
      }
      if (key === 'ShutterSpeedValue') {
        return `${result.toFixed(2)} EV`;
      }

      return value.map((v: number) => v.toString()).join(", ");
    }
  }

  // Format LensSpecification - convert nested array to readable format
  if (key === "LensSpecification" && Array.isArray(value)) {
    try {
      // LensSpecification format: [[id, min_focal], [id, max_focal], [id, min_aperture], [id, max_aperture]]
      // Each pair has a constant identifier (usually 4) and the actual value
      // We extract the second element (index 1) which contains the specification value
      const values = value.map((v) => (Array.isArray(v) && v.length >= 2 ? v[1] : v));
      if (values.length >= 4) {
        const minFocal = parseFloat(values[0]);
        const maxFocal = parseFloat(values[1]);
        const minAperture = parseFloat(values[2]);
        const maxAperture = parseFloat(values[3]);

        if (!isNaN(minFocal) && !isNaN(maxFocal) && !isNaN(minAperture) && !isNaN(maxAperture)) {
          // Format as "min-max mm, f/aperture-aperture"
          const focalRange = minFocal === maxFocal
            ? `${minFocal.toFixed(1)}mm`
            : `${minFocal.toFixed(1)}-${maxFocal.toFixed(1)}mm`;
          const apertureRange = minAperture === maxAperture
            ? `ƒ/${minAperture.toFixed(1)}`
            : `ƒ/${minAperture.toFixed(1)}-${maxAperture.toFixed(1)}`;
          return `${focalRange}, ${apertureRange}`;
        }
      }
    } catch (e) {
      // Fall back to string representation
    }
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
    return `ƒ/${num.toFixed(1)}`;
  }

  // Format focal length
  if (key === "FocalLength" || key === "FocalLenIn35mmFilm") {
    const num = parseFloat(value);
    return `${num.toFixed(0)}mm`;
  }

  // Format ISO
  if (
    key === "ISO" ||
    key === "ISOSpeedRatings" ||
    key === "PhotographicSensitivity"
  ) {
    return `ISO ${value}`;
  }

  // Handle specific enum fields
  const enumMappings: { [key: string]: { [value: number]: string } } = {
    Flash: {
      0: 'No Flash',
      1: 'Fired',
      5: 'Fired, Return not detected',
      7: 'Fired, Return detected',
      8: 'On, Did not fire',
      9: 'On, Fired',
      13: 'On, Return not detected',
      15: 'On, Return detected',
      16: 'Off, Did not fire',
      24: 'Auto, Did not fire',
      25: 'Auto, Fired',
      29: 'Auto, Fired, Return not detected',
      31: 'Auto, Fired, Return detected'
    },
    ColorSpace: {
      1: 'sRGB',
      65535: 'Uncalibrated'
    },
    ExposureMode: {
      0: 'Auto',
      1: 'Manual',
      2: 'Auto Bracket'
    },
    MeteringMode: {
      0: 'Unknown',
      1: 'Average',
      2: 'Center Weighted Average',
      3: 'Spot',
      4: 'Multi-Spot',
      5: 'Pattern',
      6: 'Partial'
    },
    WhiteBalance: {
      0: 'Auto',
      1: 'Manual'
    },
    ExposureProgram: {
      0: 'Not Defined',
      1: 'Manual',
      2: 'Program AE',
      3: 'Aperture Priority',
      4: 'Shutter Priority',
      5: 'Creative Program',
      6: 'Action Program',
      7: 'Portrait Mode',
      8: 'Landscape Mode'
    },
    SensingMethod: {
      1: 'Not defined',
      2: 'One-chip color area',
      3: 'Two-chip color area',
      4: 'Three-chip color area',
      5: 'Color sequential area',
      7: 'Trilinear',
      8: 'Color sequential linear'
    },
    SceneType: {
      1: 'Directly photographed'
    },
    CompositeImage: {
      0: 'Unknown',
      1: 'Not a Composite',
      2: 'General Composite',
      3: 'Composite with HDR'
    }
  };

  if (enumMappings[key] && typeof value === 'number') {
    return enumMappings[key][value] || `Unknown (${value})`;
  }

  // SubjectArea
  if (key === 'SubjectArea') {
    return `[${value.join(', ')}]`;
  }

  // ExifVersion
  if (key === 'ExifVersion') {
    return value.join('.');
  }

  // Handle dimensions
  if (key === 'PixelXDimension' || key === 'PixelYDimension') {
    return `${value}px`;
  }

  // For any other numeric value, limit to 1 decimal point
  const num = parseFloat(value);
  if (!isNaN(num) && isFinite(num)) {
    // Check if it's a float with decimals
    if (num % 1 !== 0) {
      return num.toFixed(1);
    }
    return String(num);
  }

  return String(value);
};

const formatExif = (exif: Record<string, any>): { important: Record<string, string>; additional: Record<string, string> } => {
  const important: Record<string, string> = {};
  const additional: Record<string, string> = {};

  // Common EXIF fields with friendly names
  const fieldMappings: Record<string, string> = {
    Make: "Camera Make",
    Model: "Camera Model",
    FNumber: "Aperture",
    ApertureValue: "Aperture",
    ExposureTime: "Shutter Speed",
    ShutterSpeedValue: "Shutter Speed",
    ISOSpeedRatings: "ISO",
    PhotographicSensitivity: "ISO",
    FocalLength: "Focal Length",
    FocalLenIn35mmFilm: "Focal Length (35mm equiv)",
    DateTimeOriginal: "Date Taken",
    DateTime: "Modified",
    DateTimeDigitized: "Date Digitized",
    ExposureProgram: "Exposure Mode",
    ExposureBiasValue: "Exposure Compensation",
  };

  // Most important fields - shown by default
  const importantFields = [
    "Make",
    "Model",
    "LensModel",
    "LensSpecification",
    "FocalLenIn35mmFilm",
    "FNumber",
    "ApertureValue",
    "ExposureTime",
    "ShutterSpeedValue",
    "ISO",
    "ISOSpeedRatings",
    "PhotographicSensitivity",
    "Flash"
  ];

  // Create a set for quick lookup
  const importantFieldsSet = new Set(importantFields);

  // Add important fields first
  for (const key of importantFields) {
    if (exif[key] !== null && exif[key] !== undefined && exif[key] !== "") {
      const displayKey = fieldMappings[key] || formatExifKey(key);
      const formattedValue = formatExifValue(key, exif[key]);
      if (formattedValue && !important[displayKey]) {
        important[displayKey] = formattedValue;
      }
    }
  }

  // Add remaining fields to additional
  for (const [key, value] of Object.entries(exif)) {
    if (value !== null && value !== undefined && value !== "") {
      const displayKey = fieldMappings[key] || formatExifKey(key);
      // Skip if already in important fields
      if (!importantFieldsSet.has(key) && !important[displayKey]) {
        const formattedValue = formatExifValue(key, value);
        if (formattedValue) {
          additional[displayKey] = formattedValue;
        }
      }
    }
  }

  return { important, additional };
};

const formattedExif = computed(() => {
  if (!photo.value?.exif) {
    return { important: {}, additional: {} };
  }
  return formatExif(photo.value.exif);
});

const hasPhotoProperties = computed(() => {
  if (!photo.value) return false;
  return (
    photo.value.favorite ||
    photo.value.hidden ||
    photo.value.isphoto ||
    photo.value.ismovie ||
    photo.value.burst ||
    photo.value.live_photo ||
    photo.value.portrait ||
    photo.value.screenshot ||
    photo.value.slow_mo ||
    photo.value.time_lapse ||
    photo.value.hdr ||
    photo.value.selfie ||
    photo.value.panorama
  );
});

onMounted(() => {
  loadPhoto();
});
</script>

<style scoped>
.photo-detail-page {
  min-height: 100vh;
  background: #121212;
  padding: 2rem;
}

.back-button-container {
  max-width: 1400px;
  margin: 0 auto 1rem;
}

.back-button {
  padding: 0.75rem 1.5rem;
  background: #2a2a2a;
  color: #e0e0e0;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s;
}

.back-button:hover {
  background: #3a3a3a;
  border-color: #667eea;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #e0e0e0;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #e0e0e0;
  text-align: center;
}

.error-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.error-state h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #ff6b6b;
}

.error-state p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.8;
}

.back-button-alt {
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
}

.back-button-alt:hover {
  background: #5568d3;
}

.detail-container {
  max-width: 1600px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 3fr 1fr;
  gap: 2rem;
  background: #1e1e1e;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

@media (max-width: 1024px) {
  .detail-container {
    grid-template-columns: 1fr;
  }
}

.image-section {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  padding: 2rem;
}

.image-section img {
  max-width: 100%;
  max-height: calc(100vh - 6rem);
  object-fit: contain;
  border-radius: 8px;
}

.metadata-section {
  padding: 2rem;
  overflow-y: auto;
  max-height: calc(100vh - 8rem);
}

.photo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 2rem;
}

.photo-header h2 {
  font-size: 1.5rem;
  color: #e0e0e0;
  margin: 0;
  word-break: break-word;
  flex: 1;
}

.share-button {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.2s;
  white-space: nowrap;
}

.share-button:hover {
  background: #5568d3;
}

.metadata-group {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #3a3a3a;
}

.metadata-group:last-child {
  border-bottom: none;
}

.metadata-group h3 {
  font-size: 1.1rem;
  color: #b0b0b0;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metadata-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.metadata-item .label {
  color: #888;
  font-weight: 600;
  min-width: 120px;
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
  padding: 0.4rem 0.8rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  color: #e0e0e0;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
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

.exif-data {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Metadata scrollbar styling */
.metadata-section::-webkit-scrollbar {
  width: 6px;
}

.metadata-section::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.metadata-section::-webkit-scrollbar-thumb {
  background: #3a3a3a;
  border-radius: 3px;
}

.metadata-section::-webkit-scrollbar-thumb:hover {
  background: #4a4a4a;
}

.map-container {
  margin-top: 1rem;
  height: 300px;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #3a3a3a;
}

/* EXIF details disclosure */
.exif-details {
  margin-top: 1rem;
}

.exif-details summary {
  cursor: pointer;
  color: #667eea;
  font-weight: 500;
  padding: 0.5rem 0;
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
}

.exif-details summary::-webkit-details-marker {
  display: none;
}

.exif-details summary::before {
  content: "▶";
  display: inline-block;
  margin-right: 0.5rem;
  transition: transform 0.2s;
  font-size: 0.75rem;
}

.exif-details[open] summary::before {
  transform: rotate(90deg);
}

.exif-details summary:hover {
  color: #7c8ef8;
}

.exif-details[open] {
  margin-bottom: 0.5rem;
}

.exif-details[open] .metadata-item:first-of-type {
  margin-top: 0.75rem;
}
</style>
