<template>
  <div class="version-page">
    <h1>Version Information</h1>

    <div class="version-info">
      <div class="info-section">
        <h2>Backend</h2>
        <div v-if="backendLoading">Loading...</div>
        <div v-else-if="backendError" class="error">
          Error loading backend version: {{ backendError }}
        </div>
        <div v-else class="info-details">
          <div class="info-row">
            <span class="info-label">Version:</span>
            <span class="info-value">{{ backendVersion?.version || 'unknown' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Git SHA:</span>
            <span class="info-value code">{{ backendVersion?.git_sha || 'unknown' }}</span>
          </div>
        </div>
      </div>

      <div class="info-section">
        <h2>Frontend</h2>
        <div class="info-details">
          <div class="info-row">
            <span class="info-label">Git SHA:</span>
            <span class="info-value code">{{ frontendGitSha }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="$router.push('/')" class="btn-back">Back to Gallery</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getVersion, getClientGitSha } from '../api/version';
import type { VersionResponse } from '../api/version';

const backendVersion = ref<VersionResponse | null>(null);
const backendLoading = ref(true);
const backendError = ref<string | null>(null);
const frontendGitSha = ref<string>(getClientGitSha());

onMounted(async () => {
  try {
    backendVersion.value = await getVersion();
  } catch (error) {
    backendError.value = error instanceof Error ? error.message : 'Unknown error';
  } finally {
    backendLoading.value = false;
  }
});
</script>

<style scoped>
.version-page {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 2rem;
  color: #333;
}

.version-info {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  margin-bottom: 2rem;
}

.info-section {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
}

.info-section h2 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #555;
  font-size: 1.3rem;
}

.info-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.info-label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
}

.info-value {
  color: #333;
}

.info-value.code {
  font-family: 'Courier New', monospace;
  background: #f5f5f5;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.error {
  color: #d9534f;
  padding: 0.5rem;
  background: #f2dede;
  border-radius: 4px;
}

.actions {
  display: flex;
  gap: 1rem;
}

.btn-back {
  padding: 0.75rem 1.5rem;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #357abd;
}
</style>
