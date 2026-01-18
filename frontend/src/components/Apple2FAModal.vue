<template>
  <div class="modal-overlay" @click.self="handleClose">
    <div class="modal-card">
      <h2>🔐 Enter 2FA Code</h2>

      <p class="modal-description">
        A verification code has been sent to your trusted device(s).
        Please enter the 6-digit code below.
      </p>

      <!-- Error message -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Success message -->
      <div v-if="success" class="success-message">
        Authentication successful! Closing...
      </div>

      <form v-if="!success" @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="code">Verification Code</label>
          <input
            id="code"
            v-model="code"
            type="text"
            inputmode="numeric"
            pattern="[0-9]*"
            maxlength="6"
            required
            placeholder="000000"
            autocomplete="one-time-code"
            :disabled="submitting"
            autofocus
          />
        </div>

        <div class="modal-actions">
          <button
            type="button"
            @click="handleClose"
            class="btn-cancel"
            :disabled="submitting"
          >
            Cancel
          </button>
          <button type="submit" class="btn-submit" :disabled="submitting || code.length !== 6">
            {{ submitting ? 'Verifying...' : 'Verify' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { submit2FACode } from '../api/apple';
import { formatApiError, logError } from '../utils/errorHandling';

interface Props {
  sessionToken: string;
}

interface Emits {
  (e: 'success'): void;
  (e: 'close'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const code = ref('');
const error = ref('');
const success = ref(false);
const submitting = ref(false);

const handleSubmit = async () => {
  error.value = '';
  submitting.value = true;

  try {
    const response = await submit2FACode({
      session_token: props.sessionToken,
      code: code.value,
    });

    if (response.success) {
      success.value = true;
      // Wait a moment before closing to show success message
      setTimeout(() => {
        emit('success');
      }, 1500);
    } else {
      error.value = response.message || 'Invalid verification code. Please try again.';
    }
  } catch (err) {
    logError('Submit2FA', err);
    error.value = formatApiError(err);
  } finally {
    submitting.value = false;
  }
};

const handleClose = () => {
  if (!submitting.value && !success.value) {
    emit('close');
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 400px;
}

.modal-card h2 {
  color: #e0e0e0;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.modal-description {
  color: #b0b0b0;
  margin-bottom: 1.5rem;
  line-height: 1.5;
}

.error-message {
  background-color: #d32f2f;
  color: white;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.success-message {
  background-color: #388e3c;
  color: white;
  padding: 0.75rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #e0e0e0;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 1.5rem;
  text-align: center;
  letter-spacing: 0.5rem;
  font-family: monospace;
}

.form-group input:focus {
  outline: none;
  border-color: #1976d2;
}

.form-group input::placeholder {
  color: #666;
  letter-spacing: 0.3rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-cancel,
.btn-submit {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.btn-cancel {
  background: #757575;
  color: white;
}

.btn-cancel:hover:not(:disabled) {
  background: #616161;
}

.btn-submit {
  background: #1976d2;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #1565c0;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
