<template>
  <div class="register-container">
    <div class="register-card">
      <h2>📷 Create Account</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="reg-username">Username</label>
          <input id="reg-username" v-model="username" type="text" required autocomplete="username"
            placeholder="Choose a username" />
        </div>

        <div class="form-group">
          <label for="reg-email">Email</label>
          <input id="reg-email" v-model="email" type="email" required autocomplete="email"
            placeholder="Enter your email" />
        </div>

        <div class="form-group">
          <label for="reg-name">Name (Optional)</label>
          <input id="reg-name" v-model="name" type="text" autocomplete="name" placeholder="Enter your name" />
        </div>

        <div class="form-group">
          <label for="reg-password">Password</label>
          <input id="reg-password" v-model="password" type="password" required autocomplete="new-password"
            placeholder="Choose a password" />
        </div>

        <div class="form-group">
          <label for="reg-password-confirm">Confirm Password</label>
          <input id="reg-password-confirm" v-model="passwordConfirm" type="password" required
            autocomplete="new-password" placeholder="Confirm your password" />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <button type="submit" :disabled="loading" class="register-button">
          {{ loading ? "Creating account..." : "Register" }}
        </button>
      </form>

      <div class="login-link">
        <p>
          Already have an account?
          <a href="#" @click.prevent="$emit('switch-to-login')">Login</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { register } from "../api/auth";

interface RegisterEmits {
  (e: "register-success"): void;
  (e: "switch-to-login"): void;
}

const emit = defineEmits<RegisterEmits>();

const username = ref<string>("");
const email = ref<string>("");
const name = ref<string>("");
const password = ref<string>("");
const passwordConfirm = ref<string>("");
const error = ref<string>("");
const success = ref<string>("");
const loading = ref<boolean>(false);

const handleRegister = async () => {
  error.value = "";
  success.value = "";

  // Validate passwords match
  if (password.value !== passwordConfirm.value) {
    error.value = "Passwords do not match";
    return;
  }

  // Validate password length
  if (password.value.length < 8) {
    error.value = "Password must be at least 8 characters long";
    return;
  }

  loading.value = true;

  try {
    await register(username.value, email.value, password.value, name.value);
    success.value = "Account created successfully! Redirecting to login...";
    // Emit register-success after a brief moment to show the success message
    setTimeout(() => {
      emit("register-success");
    }, 1000);
  } catch (err: any) {
    console.error("Registration error:", err);
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else {
      error.value = "An error occurred. Please try again.";
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #121212;
  padding: 1rem;
}

.register-card {
  background: #1e1e1e;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  width: 100%;
  max-width: 400px;
}

.register-card h2 {
  color: #e0e0e0;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.8rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #b0b0b0;
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.error-message {
  background: #ff4444;
  color: white;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.success-message {
  background: #44aa44;
  color: white;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.register-button {
  width: 100%;
  padding: 0.75rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
}

.register-button:hover:not(:disabled) {
  background: #5568d3;
}

.register-button:disabled {
  background: #4a4a4a;
  cursor: not-allowed;
}

.login-link {
  margin-top: 1.5rem;
  text-align: center;
}

.login-link p {
  color: #b0b0b0;
  font-size: 0.9rem;
}

.login-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
