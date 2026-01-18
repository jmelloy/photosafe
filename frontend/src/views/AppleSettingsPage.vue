<template>
  <div class="settings-container">
    <div class="settings-card">
      <h2>🍎 Apple/iCloud Settings</h2>

      <!-- Error message -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Success message -->
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="loading">
        <p>Loading credentials...</p>
      </div>

      <!-- Credentials list -->
      <div v-else-if="credentials.length > 0" class="credentials-list">
        <h3>Your Apple Accounts</h3>
        <div v-for="credential in credentials" :key="credential.id" class="credential-item">
          <div class="credential-info">
            <div class="credential-email">{{ credential.apple_id }}</div>
            <div class="credential-status">
              <span v-if="credential.is_active" class="status-badge active">Active</span>
              <span v-else class="status-badge inactive">Inactive</span>
              <span v-if="credential.requires_2fa" class="status-badge requires-2fa">2FA</span>
              <span v-if="credential.last_authenticated_at" class="last-auth">
                Last auth: {{ formatDate(credential.last_authenticated_at) }}
              </span>
            </div>
          </div>
          <div class="credential-actions">
            <button @click="initiateAuth(credential.id)" class="btn-auth" :disabled="authenticating">
              {{ authenticating ? 'Authenticating...' : 'Authenticate' }}
            </button>
            <button @click="deleteCredential(credential.id)" class="btn-delete">
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Add new credential form -->
      <div class="add-credential-section">
        <h3>{{ credentials.length > 0 ? 'Add Another Account' : 'Add Your Apple Account' }}</h3>
        <form @submit.prevent="handleAddCredential">
          <div class="form-group">
            <label for="apple-id">Apple ID (Email)</label>
            <input
              id="apple-id"
              v-model="newAppleId"
              type="email"
              required
              placeholder="your@icloud.com"
              autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label for="password">App-Specific Password</label>
            <input
              id="password"
              v-model="newPassword"
              type="password"
              required
              placeholder="xxxx-xxxx-xxxx-xxxx"
              autocomplete="new-password"
            />
            <small class="help-text">
              Generate an app-specific password at
              <a href="https://appleid.apple.com" target="_blank">appleid.apple.com</a>
            </small>
          </div>

          <button type="submit" :disabled="saving" class="btn-save">
            {{ saving ? 'Saving...' : 'Save Credentials' }}
          </button>
        </form>
      </div>
    </div>

    <!-- 2FA Modal -->
    <Apple2FAModal
      v-if="show2FAModal"
      :session-token="currentSessionToken"
      @success="handle2FASuccess"
      @close="close2FAModal"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  listAppleCredentials,
  createAppleCredential,
  deleteAppleCredential as deleteAppleCredentialAPI,
  initiateAppleAuth,
  type AppleCredential,
} from '../api/apple';
import { formatApiError, logError } from '../utils/errorHandling';
import Apple2FAModal from '../components/Apple2FAModal.vue';

const credentials = ref<AppleCredential[]>([]);
const loading = ref(false);
const saving = ref(false);
const authenticating = ref(false);
const error = ref('');
const successMessage = ref('');
const newAppleId = ref('');
const newPassword = ref('');
const show2FAModal = ref(false);
const currentSessionToken = ref('');

const formatDate = (dateString: string | null): string => {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
};

const loadCredentials = async () => {
  loading.value = true;
  error.value = '';
  try {
    credentials.value = await listAppleCredentials();
  } catch (err) {
    logError('LoadCredentials', err);
    error.value = formatApiError(err);
  } finally {
    loading.value = false;
  }
};

const handleAddCredential = async () => {
  saving.value = true;
  error.value = '';
  successMessage.value = '';
  try {
    await createAppleCredential({
      apple_id: newAppleId.value,
      password: newPassword.value,
    });
    successMessage.value = 'Credentials saved successfully!';
    newAppleId.value = '';
    newPassword.value = '';
    await loadCredentials();
  } catch (err) {
    logError('AddCredential', err);
    error.value = formatApiError(err);
  } finally {
    saving.value = false;
  }
};

const deleteCredential = async (credentialId: number) => {
  if (!confirm('Are you sure you want to delete this credential?')) {
    return;
  }

  error.value = '';
  successMessage.value = '';
  try {
    await deleteAppleCredentialAPI(credentialId);
    successMessage.value = 'Credential deleted successfully!';
    await loadCredentials();
  } catch (err) {
    logError('DeleteCredential', err);
    error.value = formatApiError(err);
  }
};

const initiateAuth = async (credentialId: number) => {
  authenticating.value = true;
  error.value = '';
  successMessage.value = '';
  try {
    const session = await initiateAppleAuth(credentialId);

    if (session.awaiting_2fa_code) {
      // Show 2FA modal
      currentSessionToken.value = session.session_token || '';
      show2FAModal.value = true;
    } else if (session.is_authenticated) {
      successMessage.value = 'Authentication successful!';
      await loadCredentials();
    } else {
      error.value = 'Authentication failed. Please check your credentials.';
    }
  } catch (err) {
    logError('InitiateAuth', err);
    error.value = formatApiError(err);
  } finally {
    authenticating.value = false;
  }
};

const handle2FASuccess = async () => {
  successMessage.value = '2FA authentication successful!';
  show2FAModal.value = false;
  await loadCredentials();
};

const close2FAModal = () => {
  show2FAModal.value = false;
  currentSessionToken.value = '';
};

onMounted(() => {
  loadCredentials();
});
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background: #121212;
  padding: 2rem;
}

.settings-card {
  max-width: 800px;
  margin: 0 auto;
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.settings-card h2 {
  color: #e0e0e0;
  margin-bottom: 1.5rem;
  font-size: 1.8rem;
}

.settings-card h3 {
  color: #e0e0e0;
  margin-bottom: 1rem;
  font-size: 1.3rem;
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
}

.loading {
  color: #e0e0e0;
  text-align: center;
  padding: 2rem;
}

.credentials-list {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #333;
}

.credential-item {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.credential-info {
  flex: 1;
}

.credential-email {
  color: #e0e0e0;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.credential-status {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.active {
  background: #388e3c;
  color: white;
}

.status-badge.inactive {
  background: #757575;
  color: white;
}

.status-badge.requires-2fa {
  background: #1976d2;
  color: white;
}

.last-auth {
  color: #999;
  font-size: 0.85rem;
}

.credential-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-auth,
.btn-delete,
.btn-save {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.btn-auth {
  background: #1976d2;
  color: white;
}

.btn-auth:hover:not(:disabled) {
  background: #1565c0;
}

.btn-delete {
  background: #d32f2f;
  color: white;
}

.btn-delete:hover {
  background: #c62828;
}

.btn-save {
  background: #388e3c;
  color: white;
  width: 100%;
  margin-top: 1rem;
}

.btn-save:hover:not(:disabled) {
  background: #2e7d32;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.add-credential-section {
  margin-top: 2rem;
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
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #1976d2;
}

.help-text {
  display: block;
  margin-top: 0.5rem;
  color: #999;
  font-size: 0.85rem;
}

.help-text a {
  color: #1976d2;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}
</style>
