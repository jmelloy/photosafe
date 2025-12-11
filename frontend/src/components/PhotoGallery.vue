<template>
  <div class="gallery-container">
    <div class="gallery-header">
      <h2>Photo Gallery</h2>
      <p class="photo-count" v-if="!loading && photos.length > 0">
        Showing {{ photos.length }} photos
      </p>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading photos...</p>
    </div>

    <div v-else-if="photos.length === 0" class="empty-state">
      <svg
        class="empty-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
      <p>No photos yet. Upload your first photo!</p>
    </div>

    <div v-else>
      <div class="photo-grid">
        <div v-for="photo in photos" :key="photo.uuid" class="photo-card">
          <div class="photo-wrapper">
            <img
              :src="photo.url"
              :alt="photo.original_filename"
              class="photo-image"
              @click="openPhoto(photo)"
            />
          </div>
          <div class="photo-info">
            <p class="photo-name" :title="photo.original_filename">
              {{ photo.original_filename }}
            </p>
            <p class="photo-date">{{ formatDate(photo.uploaded_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Infinite scroll trigger -->
      <div ref="loadMoreTrigger" class="load-more-trigger" v-if="hasMore">
        <div v-if="loadingMore" class="loading-more">
          <div class="spinner-small"></div>
          <p>Loading more photos...</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from "vue";
import { useRouter } from "vue-router";
import type { Photo } from "../types/api";

interface PhotoGalleryProps {
  photos: Photo[];
  loading?: boolean;
  loadingMore?: boolean;
  hasMore?: boolean;
}

interface PhotoGalleryEmits {
  (e: "delete-photo", id: string): void;
  (e: "load-more"): void;
}

const props = defineProps<PhotoGalleryProps>();
const emit = defineEmits<PhotoGalleryEmits>();
const router = useRouter();

const loadMoreTrigger = ref<HTMLElement | null>(null);
let observer: IntersectionObserver | null = null;

const formatDate = (dateString?: string): string => {
  if (!dateString) return "Unknown";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const openPhoto = (photo: Photo): void => {
  // Navigate to photo detail page
  router.push(`/photos/${photo.uuid}`);
};

const setupIntersectionObserver = () => {
  // Disconnect any existing observer first
  if (observer) {
    observer.disconnect();
  }

  if (!loadMoreTrigger.value || !props.hasMore) {
    return;
  }

  observer = new IntersectionObserver(
    (entries) => {
      const [entry] = entries;
      if (entry.isIntersecting && props.hasMore && !props.loadingMore) {
        emit("load-more");
      }
    },
    {
      root: null,
      rootMargin: "200px", // Load more when within 200px of trigger
      threshold: 0.1,
    }
  );

  observer.observe(loadMoreTrigger.value);
};

onMounted(() => {
  setupIntersectionObserver();
});

// Re-setup observer when hasMore changes from false to true
watch(() => props.hasMore, (newHasMore, oldHasMore) => {
  if (newHasMore && !oldHasMore) {
    setupIntersectionObserver();
  } else if (!newHasMore && observer) {
    // Disconnect observer when hasMore becomes false
    observer.disconnect();
  }
});

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect();
  }
});
</script>

<style scoped>
.gallery-container {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.gallery-header h2 {
  margin: 0;
  color: #e0e0e0;
}

.photo-count {
  color: #b0b0b0;
  font-size: 0.95rem;
  margin: 0;
}

.loading,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: #b0b0b0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #3a3a3a;
  border-top: 4px solid #667eea;
  border-radius: 50%;
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
  width: 96px;
  height: 96px;
  color: #4a4a4a;
  margin-bottom: 1rem;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.photo-card {
  background: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.photo-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.photo-wrapper {
  position: relative;
  padding-top: 100%;
  overflow: hidden;
  background: #1a1a1a;
}

.photo-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.photo-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.photo-card:hover .photo-overlay {
  opacity: 1;
}

.delete-button {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}

.delete-button:hover {
  background: #dc2626;
}

.delete-button svg {
  width: 24px;
  height: 24px;
}

.photo-info {
  padding: 1rem;
}

.photo-name {
  font-weight: 500;
  color: #e0e0e0;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.photo-date {
  font-size: 0.875rem;
  color: #b0b0b0;
}

.load-more-trigger {
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2rem;
}

.loading-more {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #b0b0b0;
}

.spinner-small {
  width: 32px;
  height: 32px;
  border: 3px solid #3a3a3a;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style>
