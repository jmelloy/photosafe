<template>
  <div class="upload-container">
    <div class="upload-card">
      <h2>Upload Photo</h2>

      <div class="drop-zone" :class="{ 'drag-over': isDragging }" @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false" @drop.prevent="handleDrop" @click="triggerFileInput">
        <div v-if="!uploading" class="drop-zone-content">
          <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p class="upload-text">Click or drag & drop to upload</p>
          <p class="upload-hint">PNG, JPG, GIF up to 10MB</p>
        </div>

        <div v-else class="uploading">
          <LoadingSpinner message="Uploading..." />
        </div>
      </div>

      <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="handleFileSelect" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { uploadPhoto } from "../api/photos";
import LoadingSpinner from "./LoadingSpinner.vue";

interface PhotoUploadEmits {
  (e: "photo-uploaded"): void;
}

const emit = defineEmits<PhotoUploadEmits>();

const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref<boolean>(false);
const uploading = ref<boolean>(false);

const triggerFileInput = (): void => {
  fileInput.value?.click();
};

const handleFileSelect = async (event: Event): Promise<void> => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    await uploadFile(file);
  }
};

const handleDrop = async (event: DragEvent): Promise<void> => {
  isDragging.value = false;
  const file = event.dataTransfer?.files[0];
  if (file && file.type.startsWith("image/")) {
    await uploadFile(file);
  } else {
    alert("Please drop an image file");
  }
};

const uploadFile = async (file: File): Promise<void> => {
  uploading.value = true;
  try {
    await uploadPhoto(file);
    emit("photo-uploaded");
    // Reset file input
    if (fileInput.value) {
      fileInput.value.value = "";
    }
  } catch (error) {
    console.error("Upload failed:", error);
    alert("Upload failed. Please try again.");
  } finally {
    uploading.value = false;
  }
};
</script>

<style scoped>
.upload-container {
  margin-bottom: 2rem;
}

.upload-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.upload-card h2 {
  margin-bottom: 1.5rem;
  color: #333;
}

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.drop-zone:hover,
.drop-zone.drag-over {
  border-color: #667eea;
  background: #f0f4ff;
}

.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  width: 64px;
  height: 64px;
  color: #667eea;
}

.upload-text {
  font-size: 1.2rem;
  font-weight: 500;
  color: #333;
}

.upload-hint {
  font-size: 0.9rem;
  color: #666;
}

.uploading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}
</style>
