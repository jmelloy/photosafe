<template>
  <div class="loading-container" :class="containerClass">
    <div class="spinner" :class="spinnerClass"></div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
interface LoadingSpinnerProps {
  message?: string;
  size?: "small" | "medium" | "large";
  containerClass?: string;
}

const props = withDefaults(defineProps<LoadingSpinnerProps>(), {
  size: "medium",
});

const spinnerClass = {
  "spinner-small": props.size === "small",
  "spinner-large": props.size === "large",
};
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #b0b0b0;
}

.spinner {
  border: 4px solid #3a3a3a;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
}

.spinner-small {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

.spinner-large {
  width: 64px;
  height: 64px;
  border-width: 5px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-message {
  margin-top: 1rem;
  font-size: 1rem;
}
</style>
