<template>
  <div class="map-view">
    <div class="map-view-header">
      <h1>📍 Photo Map</h1>
      <button @click="goBack" class="back-button">← Back to Gallery</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading photos with location data...</p>
    </div>

    <!-- No photos state -->
    <div v-else-if="!loading && photos.length === 0" class="empty-state">
      <div class="empty-icon">📍</div>
      <h2>No Photos with Location Data</h2>
      <p>Photos with GPS coordinates will appear on this map.</p>
      <button @click="goBack" class="back-button-alt">Go Back to Gallery</button>
    </div>

    <!-- Map view -->
    <div v-else class="map-container">
      <div ref="mapContainer" class="map"></div>

      <!-- Photo preview card -->
      <div v-if="selectedPhoto" class="photo-preview-card">
        <button @click="closePreview" class="preview-close">×</button>
        <img
          :src="selectedPhoto.url"
          :alt="selectedPhoto.original_filename"
          class="preview-image"
        />
        <div class="preview-info">
          <h3>{{ selectedPhoto.original_filename }}</h3>
          <p v-if="selectedPhoto.date" class="preview-date">
            {{ formatDate(selectedPhoto.date) }}
          </p>
          <button @click="goToPhoto(selectedPhoto.uuid)" class="view-details-btn">
            View Details →
          </button>
        </div>
      </div>
    </div>

    <!-- Stats bar -->
    <div v-if="!loading && photos.length > 0" class="stats-bar">
      <span>📷 {{ photos.length }} photos with location data</span>
      <span>📍 {{ uniqueLocations }} unique locations</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getPhotos } from "../api/photos";
import type { Photo } from "../types/api";

const router = useRouter();
const mapContainer = ref<HTMLElement | null>(null);
const photos = ref<Photo[]>([]);
const loading = ref<boolean>(true);
const selectedPhoto = ref<Photo | null>(null);

let map: L.Map | null = null;
const markers: L.Marker[] = [];

// Group photos by location (rounded to 4 decimal places for clustering)
const groupPhotosByLocation = (photos: Photo[]) => {
  const groups = new Map<string, Photo[]>();

  photos.forEach((photo) => {
    if (photo.latitude != null && photo.longitude != null) {
      // Round to 4 decimal places (~11m precision) for clustering nearby photos
      const lat = parseFloat(photo.latitude.toFixed(4));
      const lng = parseFloat(photo.longitude.toFixed(4));
      const key = `${lat},${lng}`;

      if (!groups.has(key)) {
        groups.set(key, []);
      }
      groups.get(key)!.push(photo);
    }
  });

  return groups;
};

const uniqueLocations = computed(() => {
  return groupPhotosByLocation(photos.value).size;
});

const loadPhotos = async () => {
  loading.value = true;
  try {
    // Fetch photos with location data
    // Note: Using 1000 as a reasonable limit. For larger collections,
    // consider implementing pagination or server-side clustering.
    const response = await getPhotos(1, 1000, { has_location: true });
    // Server-side filter already ensures has_location: true returns only photos with coordinates
    photos.value = response.items;
  } catch (error) {
    console.error("Failed to load photos:", error);
  } finally {
    loading.value = false;
  }
};

const createMarkerIcon = (photoCount: number): string => {
  return `
    <div class="custom-marker">
      <div class="marker-count">${photoCount}</div>
    </div>
  `;
};

const initMap = () => {
  if (!mapContainer.value || photos.value.length === 0) return;

  // Create map
  map = L.map(mapContainer.value).setView([0, 0], 2);

  // Add OpenStreetMap tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // Group photos by location
  const photoGroups = groupPhotosByLocation(photos.value);

  // Add markers for each location group
  const bounds: L.LatLngBoundsExpression = [];
  photoGroups.forEach((groupPhotos, locationKey) => {
    const [lat, lng] = locationKey.split(",").map(parseFloat);
    bounds.push([lat, lng]);

    // Create custom icon with photo count
    const photoCount = groupPhotos.length;
    const customIcon = L.divIcon({
      html: createMarkerIcon(photoCount),
      className: "custom-marker-wrapper",
      iconSize: [40, 40],
      iconAnchor: [20, 40],
      popupAnchor: [0, -40],
    });

    const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map!);

    // On marker click, show photos at this location
    marker.on("click", () => {
      // If multiple photos at this location, show the first one
      // In a real app, you might show a list/carousel
      selectedPhoto.value = groupPhotos[0];
    });

    // Create popup content with thumbnail grid
    const popupContent = document.createElement("div");
    popupContent.className = "marker-popup";

    const title = document.createElement("div");
    title.className = "popup-title";
    title.textContent = `${photoCount} photo${photoCount > 1 ? "s" : ""} at this location`;
    popupContent.appendChild(title);

    const thumbnailGrid = document.createElement("div");
    thumbnailGrid.className = "popup-thumbnail-grid";

    // Show up to 4 thumbnails in popup
    groupPhotos.slice(0, 4).forEach((photo) => {
      const imgWrapper = document.createElement("div");
      imgWrapper.className = "popup-thumbnail";
      imgWrapper.addEventListener("click", () => {
        selectedPhoto.value = photo;
        map?.closePopup();
      });

      const img = document.createElement("img");
      img.src = photo.url || "";
      img.alt = photo.original_filename;
      imgWrapper.appendChild(img);
      thumbnailGrid.appendChild(imgWrapper);
    });

    popupContent.appendChild(thumbnailGrid);

    if (photoCount > 4) {
      const moreText = document.createElement("div");
      moreText.className = "popup-more";
      moreText.textContent = `+${photoCount - 4} more`;
      popupContent.appendChild(moreText);
    }

    marker.bindPopup(popupContent, {
      maxWidth: 300,
      className: "photo-popup",
    });

    markers.push(marker);
  });

  // Fit map to show all markers
  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [50, 50] });
  }
};

const formatDate = (dateString?: string): string => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

const goBack = () => {
  router.push("/");
};

const closePreview = () => {
  selectedPhoto.value = null;
};

const goToPhoto = (uuid: string) => {
  router.push(`/photos/${uuid}`);
};

onMounted(async () => {
  await loadPhotos();
  if (photos.value.length > 0) {
    // Wait for next tick to ensure map container is rendered
    await nextTick();
    initMap();
  }
});

onUnmounted(() => {
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<style scoped>
.map-view {
  min-height: 100vh;
  background: #121212;
  display: flex;
  flex-direction: column;
}

.map-view-header {
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1e1e1e;
  border-bottom: 1px solid #3a3a3a;
}

.map-view-header h1 {
  margin: 0;
  color: #e0e0e0;
  font-size: 2rem;
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

.loading,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #e0e0e0;
  padding: 4rem;
}

.spinner {
  border: 4px solid #3a3a3a;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  color: #e0e0e0;
}

.empty-state p {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  opacity: 0.7;
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

.map-container {
  flex: 1;
  position: relative;
  min-height: 500px;
}

.map {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.photo-preview-card {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 320px;
  background: #1e1e1e;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  overflow: hidden;
  z-index: 1000;
}

.preview-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
}

.preview-close:hover {
  background: rgba(0, 0, 0, 0.95);
}

.preview-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.preview-info {
  padding: 1rem;
}

.preview-info h3 {
  margin: 0 0 0.5rem 0;
  color: #e0e0e0;
  font-size: 1rem;
  word-break: break-word;
}

.preview-date {
  margin: 0 0 1rem 0;
  color: #b0b0b0;
  font-size: 0.875rem;
}

.view-details-btn {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.2s;
}

.view-details-btn:hover {
  background: #5568d3;
}

.stats-bar {
  padding: 1rem 2rem;
  background: #1e1e1e;
  border-top: 1px solid #3a3a3a;
  color: #b0b0b0;
  display: flex;
  gap: 2rem;
  justify-content: center;
  font-size: 0.9rem;
}
</style>

<style>
/* Global styles for Leaflet markers */
.custom-marker-wrapper {
  background: transparent;
  border: none;
}

.custom-marker {
  background: #667eea;
  border: 3px solid white;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: transform 0.2s;
}

.custom-marker:hover {
  transform: scale(1.1);
}

.marker-count {
  color: white;
  font-weight: 700;
  font-size: 14px;
}

/* Popup styling */
.photo-popup .leaflet-popup-content-wrapper {
  background: #1e1e1e;
  color: #e0e0e0;
  border-radius: 8px;
  padding: 0;
}

.photo-popup .leaflet-popup-tip {
  background: #1e1e1e;
}

.marker-popup {
  padding: 0.5rem;
}

.popup-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #e0e0e0;
  font-size: 0.9rem;
}

.popup-thumbnail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.popup-thumbnail {
  width: 100%;
  aspect-ratio: 1;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
  transition: transform 0.2s;
}

.popup-thumbnail:hover {
  transform: scale(1.05);
}

.popup-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.popup-more {
  text-align: center;
  color: #b0b0b0;
  font-size: 0.8rem;
}
</style>
