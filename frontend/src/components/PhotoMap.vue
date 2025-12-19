<template>
  <div class="photo-map-container">
    <div ref="mapContainer" class="map"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface PhotoMapProps {
  latitude?: number;
  longitude?: number;
  photoTitle?: string;
  zoom?: number;
}

const props = withDefaults(defineProps<PhotoMapProps>(), {
  zoom: 13,
});

const mapContainer = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let marker: L.Marker | null = null;

const initMap = () => {
  if (!mapContainer.value || props.latitude === undefined || props.longitude === undefined) return;

  // Create map centered on the photo location
  map = L.map(mapContainer.value).setView(
    [props.latitude, props.longitude],
    props.zoom
  );

  // Add OpenStreetMap tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  // Add marker for photo location
  marker = L.marker([props.latitude, props.longitude]).addTo(map);

  if (props.photoTitle) {
    marker.bindPopup(props.photoTitle);
  }
};

const updateMarker = () => {
  if (map && marker && props.latitude !== undefined && props.longitude !== undefined) {
    // Update marker position
    marker.setLatLng([props.latitude, props.longitude]);
    map.setView([props.latitude, props.longitude], props.zoom);

    // Update popup if title changes
    if (props.photoTitle) {
      marker.bindPopup(props.photoTitle);
    }
  }
};

onMounted(() => {
  initMap();
});

onUnmounted(() => {
  if (map) {
    map.remove();
    map = null;
  }
});

// Watch for prop changes
watch(
  () => [props.latitude, props.longitude, props.photoTitle],
  () => {
    if (map) {
      updateMarker();
    }
  }
);
</script>

<style scoped>
.photo-map-container {
  width: 100%;
  height: 100%;
  min-height: 200px;
  border-radius: 8px;
  overflow: hidden;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
