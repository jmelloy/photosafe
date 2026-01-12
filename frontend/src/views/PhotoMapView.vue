<template>
  <div class="map-view">
    <div class="map-view-header">
      <h1>📍 Photo Map</h1>
      <button @click="goBack" class="back-button">← Back to Gallery</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading">
      <LoadingSpinner message="Loading photos with location data..." />
    </div>

    <!-- No photos state -->
    <div v-else-if="!loading && placeSummaries.length === 0" class="empty-state">
      <div class="empty-icon">📍</div>
      <h2>No Photos with Location Data</h2>
      <p>Photos with GPS coordinates will appear on this map.</p>
      <button @click="goBack" class="back-button-alt">Go Back to Gallery</button>
    </div>

    <!-- Map view -->
    <div v-else class="map-container">
      <div ref="mapContainer" class="map"></div>

      <!-- Place summary card -->
      <div v-if="selectedPhoto" class="photo-preview-card">
        <button @click="closePreview" class="preview-close">×</button>
        <div class="preview-info place-info">
          <h3>{{ selectedPhoto.place_name }}</h3>
          <p v-if="selectedPhoto.city || selectedPhoto.state_province || selectedPhoto.country"
            class="preview-location">
            {{ [selectedPhoto.city, selectedPhoto.state_province, selectedPhoto.country].filter(Boolean).join(", ") }}
          </p>
          <p class="preview-count">
            📷 {{ selectedPhoto.photo_count }} photo{{ selectedPhoto.photo_count > 1 ? "s" : "" }}
          </p>
          <p v-if="selectedPhoto.first_photo_date && selectedPhoto.last_photo_date" class="preview-date">
            {{ formatDateRange(selectedPhoto.first_photo_date, selectedPhoto.last_photo_date) }}
          </p>
        </div>
      </div>
    </div>

    <!-- Stats bar -->
    <div v-if="!loading && placeSummaries.length > 0" class="stats-bar">
      <span>📷 {{ totalPhotoCount }} photos with location data</span>
      <span>📍 {{ uniqueLocations }} unique locations</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getPlaceSummaries } from "../api/places";
import type { PlaceSummary } from "../types/api";
import { formatDateRange } from "../utils/format";
import LoadingSpinner from "../components/LoadingSpinner.vue";

const router = useRouter();
const mapContainer = ref<HTMLElement | null>(null);
const placeSummaries = ref<PlaceSummary[]>([]);
const loading = ref<boolean>(true);
const selectedPhoto = ref<PlaceSummary | null>(null);

let map: L.Map | null = null;
const markers: L.Marker[] = [];

const uniqueLocations = computed(() => {
  return placeSummaries.value.length;
});

const totalPhotoCount = computed(() => {
  return placeSummaries.value.reduce((sum, summary) => sum + summary.photo_count, 0);
});

const loadPlaceSummaries = async () => {
  loading.value = true;
  try {
    // Fetch place summaries - these are pre-aggregated by the backend
    // The backend default limit is 100, but we increase it for the map view
    // to show more locations. Consider implementing pagination if needed.
    placeSummaries.value = await getPlaceSummaries({ limit: 1000 });
  } catch (error) {
    console.error("Failed to load place summaries:", error);
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
  if (!mapContainer.value || placeSummaries.value.length === 0) return;

  // Create map
  map = L.map(mapContainer.value).setView([0, 0], 2);

  // Add OpenStreetMap tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // Add markers for each place summary
  const bounds: L.LatLngBoundsExpression = [];

  placeSummaries.value.forEach((summary) => {
    if (summary.latitude == null || summary.longitude == null) return;

    const lat = summary.latitude;
    const lng = summary.longitude;
    bounds.push([lat, lng]);

    // Create custom icon with photo count
    const photoCount = summary.photo_count;
    const customIcon = L.divIcon({
      html: createMarkerIcon(photoCount),
      className: "custom-marker-wrapper",
      iconSize: [40, 40],
      iconAnchor: [20, 40],
      popupAnchor: [0, -40],
    });

    const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map!);

    // On marker click, show place summary info
    marker.on("click", () => {
      selectedPhoto.value = summary;
    });

    // Create popup content with place information
    const popupContent = document.createElement("div");
    popupContent.className = "marker-popup";

    const title = document.createElement("div");
    title.className = "popup-title";
    title.textContent = summary.place_name;
    popupContent.appendChild(title);

    const photoCountDiv = document.createElement("div");
    photoCountDiv.className = "popup-info";
    photoCountDiv.textContent = `${photoCount} photo${photoCount > 1 ? "s" : ""}`;
    popupContent.appendChild(photoCountDiv);

    if (summary.first_photo_date && summary.last_photo_date) {
      const dateRange = document.createElement("div");
      dateRange.className = "popup-info";
      const firstDate = new Date(summary.first_photo_date).getFullYear();
      const lastDate = new Date(summary.last_photo_date).getFullYear();
      if (firstDate === lastDate) {
        dateRange.textContent = `Photos from ${firstDate}`;
      } else {
        dateRange.textContent = `${firstDate} - ${lastDate}`;
      }
      popupContent.appendChild(dateRange);
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

const goBack = () => {
  router.push("/");
};

const closePreview = () => {
  selectedPhoto.value = null;
};

onMounted(async () => {
  await loadPlaceSummaries();
  if (placeSummaries.value.length > 0) {
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

.preview-info {
  padding: 1rem;
}

.place-info {
  padding: 2rem 1rem;
}

.preview-info h3 {
  margin: 0 0 0.5rem 0;
  color: #e0e0e0;
  font-size: 1.1rem;
  word-break: break-word;
}

.preview-location {
  margin: 0 0 0.75rem 0;
  color: #b0b0b0;
  font-size: 0.9rem;
}

.preview-count {
  margin: 0 0 0.5rem 0;
  color: #e0e0e0;
  font-size: 0.95rem;
  font-weight: 500;
}

.preview-date {
  margin: 0;
  color: #b0b0b0;
  font-size: 0.875rem;
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
  font-size: 0.95rem;
}

.popup-info {
  color: #b0b0b0;
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
}
</style>
