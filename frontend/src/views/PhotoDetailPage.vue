<template>
  <div class="photo-detail-page">
    <!-- Back button -->
    <div class="back-button-container">
      <button @click="goBack" class="back-button">← Back to Gallery</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading photo...</p>
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
        <img :src="photo.url" :alt="photo.original_filename" />
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
          <div class="metadata-item">
            <span class="label">UUID:</span>
            <span class="value">{{ photo.uuid }}</span>
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
        <div
          class="metadata-group"
          v-if="photo.albums && photo.albums.length > 0"
        >
          <h3>Albums</h3>
          <div class="tags">
            <span v-for="album in photo.albums" :key="album" class="tag album">
              📁 {{ album }}
            </span>
          </div>
        </div>

        <!-- Keywords -->
        <div
          class="metadata-group"
          v-if="photo.keywords && photo.keywords.length > 0"
        >
          <h3>Keywords</h3>
          <div class="tags">
            <span
              v-for="keyword in photo.keywords"
              :key="keyword"
              class="tag keyword"
            >
              🏷️ {{ keyword }}
            </span>
          </div>
        </div>

        <!-- Labels -->
        <div
          class="metadata-group"
          v-if="photo.labels && photo.labels.length > 0"
        >
          <h3>Labels</h3>
          <div class="tags">
            <span v-for="label in photo.labels" :key="label" class="tag label">
              {{ label }}
            </span>
          </div>
        </div>

        <!-- People -->
        <div
          class="metadata-group"
          v-if="photo.persons && photo.persons.length > 0"
        >
          <h3>People</h3>
          <div class="tags">
            <span
              v-for="person in photo.persons"
              :key="person"
              class="tag person"
            >
              👤 {{ person }}
            </span>
          </div>
        </div>

        <!-- Location -->
        <div class="metadata-group" v-if="photo.latitude && photo.longitude">
          <h3>Location</h3>
          <div class="metadata-item">
            <span class="label">Coordinates:</span>
            <span class="value"
              >{{ photo.latitude }}, {{ photo.longitude }}</span
            >
          </div>
          <div class="metadata-item" v-if="photo.place">
            <span class="label">Place:</span>
            <span class="value">{{ formatPlace(photo.place) }}</span>
          </div>
          <!-- Map -->
          <div class="map-container">
            <PhotoMap
              :latitude="photo.latitude"
              :longitude="photo.longitude"
              :photo-title="photo.original_filename"
            />
          </div>
        </div>

        <!-- EXIF Data -->
        <div class="metadata-group" v-if="photo.exif">
          <h3>EXIF Data</h3>
          <div class="exif-data">
            <div
              v-for="[key, value] in Object.entries(photo.exif)"
              :key="key"
              class="metadata-item"
            >
              <span class="label">{{ formatExifKey(key) }}:</span>
              <span class="value">{{ formatExifValue(value) }}</span>
            </div>
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

interface PhotoDetailPageProps {
  uuid: string;
}

const props = defineProps<PhotoDetailPageProps>();
const router = useRouter();

const photo = ref<Photo | null>(null);
const loading = ref<boolean>(true);
const error = ref<string>("");
const copyLinkText = ref<string>("🔗 Share Link");

// Type guard for Axios-like error responses
interface AxiosLikeError {
  response?: {
    status?: number;
  };
}

function isAxiosLikeError(error: unknown): error is AxiosLikeError {
  return typeof error === "object" && error !== null && "response" in error;
}

const loadPhoto = async () => {
  loading.value = true;
  error.value = "";

  try {
    photo.value = await getPhoto(props.uuid);
  } catch (err: unknown) {
    console.error("Failed to load photo:", err);
    if (isAxiosLikeError(err)) {
      if (err.response?.status === 404) {
        error.value = "The photo you're looking for doesn't exist.";
      } else if (err.response?.status === 403) {
        error.value = "You don't have permission to view this photo.";
      } else {
        error.value = "Failed to load photo. Please try again.";
      }
    } else {
      error.value = "Failed to load photo. Please try again.";
    }
  } finally {
    loading.value = false;
  }
};

const goBack = () => {
  router.push("/");
};

const copyLink = async () => {
  const url = window.location.href;
  try {
    await navigator.clipboard.writeText(url);
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
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(2)} MB`;
};

const formatPlace = (place: unknown): string => {
  if (typeof place === "string") return place;
  if (place && typeof place === "object") {
    // Only show top-level fields, excluding nested objects like "names" and "address"
    const placeObj = place as Record<string, any>;
    const parts: string[] = [];
    
    // Show the main name if available
    if (placeObj.name) {
      parts.push(placeObj.name);
    }
    
    // Show address_str if available (more readable than nested address object)
    if (placeObj.address_str) {
      parts.push(`Address: ${placeObj.address_str}`);
    }
    
    // Show if it's home
    if (placeObj.ishome === true) {
      parts.push("(Home)");
    }
    
    // Show country code
    if (placeObj.country_code) {
      parts.push(`Country: ${placeObj.country_code}`);
    }
    
    return parts.join(" | ") || "Location information available";
  }
  return "";
};

const formatExifKey = (key: string): string => {
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

const formatExifValue = (value: any): string => {
  if (value === null || value === undefined || value === "") {
    return "";
  }

  // For numeric values, limit to 1 decimal point
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

.spinner {
  border: 4px solid #3a3a3a;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
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
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 400px;
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
  max-height: calc(100vh - 8rem);
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
  background: #ffd700;
  color: #000;
  border-color: #ffd700;
}

.tag.album {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.tag.keyword {
  background: #48bb78;
  color: white;
  border-color: #48bb78;
}

.tag.person {
  background: #ed64a6;
  color: white;
  border-color: #ed64a6;
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
</style>
