<template>
  <div class="gallery-container">
    <h2>Photo Gallery</h2>

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

    <div v-else class="photo-grid">
      <div v-for="photo in photos" :key="photo.id" class="photo-card">
        <div class="photo-wrapper">
          <img
            :src="photo.url"
            :alt="photo.original_filename"
            class="photo-image"
            @click="openPhoto(photo)"
          />
          <div class="photo-overlay">
            <button
              @click.stop="$emit('delete-photo', photo.id)"
              class="delete-button"
              title="Delete photo"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
        <div class="photo-info">
          <p class="photo-name" :title="photo.original_filename">
            {{ photo.original_filename }}
          </p>
          <p class="photo-date">{{ formatDate(photo.uploaded_at) }}</p>
        </div>
      </div>
    </div>

    <!-- Modal for full-size photo view -->
    <div v-if="selectedPhoto" class="modal" @click="closePhoto">
      <div class="modal-content" @click.stop>
        <button class="modal-close" @click="closePhoto">×</button>
        <img :src="selectedPhoto.url" :alt="selectedPhoto.original_filename" />
        <div class="modal-info">
          <h3>{{ selectedPhoto.original_filename }}</h3>
          <p>Uploaded: {{ formatDate(selectedPhoto.uploaded_at) }}</p>
          <p>Size: {{ formatFileSize(selectedPhoto.file_size) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";

export default {
  name: "PhotoGallery",
  props: {
    photos: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["delete-photo"],
  setup() {
    const selectedPhoto = ref(null);

    const formatDate = (dateString) => {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    };

    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
      return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    };

    const openPhoto = (photo) => {
      selectedPhoto.value = photo;
    };

    const closePhoto = () => {
      selectedPhoto.value = null;
    };

    return {
      selectedPhoto,
      formatDate,
      formatFileSize,
      openPhoto,
      closePhoto,
    };
  },
};
</script>

<style scoped>
.gallery-container {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.gallery-container h2 {
  margin-bottom: 1.5rem;
  color: #e0e0e0;
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

/* Modal styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  background: #2a2a2a;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-content img {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 2rem;
  line-height: 1;
  cursor: pointer;
  z-index: 1;
}

.modal-close:hover {
  background: rgba(0, 0, 0, 0.7);
}

.modal-info {
  padding: 1.5rem;
  background: #2a2a2a;
}

.modal-info h3 {
  margin-bottom: 0.5rem;
  color: #e0e0e0;
}

.modal-info p {
  color: #b0b0b0;
  margin-bottom: 0.25rem;
}
</style>
